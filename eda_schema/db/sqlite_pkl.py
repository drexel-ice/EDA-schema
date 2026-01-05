from pathlib import Path
import sqlite3
import dill
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from eda_schema import entity
from eda_schema.db.base import BaseDB
from eda_schema.errors import DataNotFoundError
from eda_schema.base import resolve_field_type_and_nullable, Image2D


def sqlite_type_from_type(type_name: Optional[str]) -> Optional[str]:
    """
    Convert a primitive type name into a SQLite column type.

    Args:
        type_name (str | None): Resolved primitive type name.

    Returns:
        str | None: SQLite type name, or None if unsupported.
    """
    mapping = {
        "string": "TEXT",
        "number": "REAL",
        "integer": "INTEGER",
        "boolean": "INTEGER",
    }

    return mapping.get(type_name)


class SQLitePickleDB(BaseDB):
    """
    Storage class using SQLite for table data and pickle files for graph data.
    """

    def __init__(self, data_dir: str | Path):
        """
        Initialize the database connection and graph storage directory.

        Args:
            data_dir (str | Path): Base directory for the SQLite DB and graph files.
        """
        data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

        self.data_dir = data_dir  # Store for image methods
        self.conn = sqlite3.connect(data_dir / "tabular.db")
        self.cursor = self.conn.cursor()

        self.graph_dir = data_dir / "graph_dir"
        self.graph_dir.mkdir(parents=True, exist_ok=True)

    def create_dataset_tables(self):
        """
        Create SQLite tables for all entities.

        Returns:
            None
        """
        for entity_name, model_cls in entity.SchemaMetadata.items():
            columns = []
            for field in entity.SchemaMetadata.get_fields(entity_name):
                type_name, is_nullable, _ = resolve_field_type_and_nullable(model_cls, field)
                sqlite_type = sqlite_type_from_type(type_name)
                if sqlite_type is None:
                    continue
                null_constraint = "NULL" if is_nullable else "NOT NULL"
                columns.append(f"{field.name} {sqlite_type} {null_constraint}")

            if not columns:
                continue

            column_defs = ", ".join(columns)
            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {entity_name} ({column_defs});"
            )

        self.conn.commit()

    def add_graph_data(self, entity_name: str, graph: Any, key: str = None, **key_fields) -> None:
        """
        Store graph data as a pickle file.

        Args:
            entity_name (str): Name of the entity.
            graph (Any): Graph object to store.
            key (str, optional): Unique graph identifier (legacy API, deprecated).
            **key_fields: Primary key values (preferred API, for consistency with ParquetDB).

        Returns:
            None

        Note:
            Supports both legacy `key: str` API (deprecated) and new `**key_fields` API.
            The `key` parameter is maintained for backward compatibility but will be
            removed in a future version. Use `**key_fields` instead.
        """
        resolved_key = self._resolve_graph_key(key, key_fields)
        filepath = self.graph_dir / f"{entity_name}_{resolved_key}.pkl"
        with filepath.open("wb") as f:
            dill.dump(graph, f)

    def get_graph_data(self, entity_name: str, key: str = None, **key_fields) -> Any:
        """
        Load stored graph data.

        Args:
            entity_name (str): Name of the entity.
            key (str, optional): Unique graph identifier (legacy API, deprecated).
            **key_fields: Primary key values (preferred API, used by BaseDB.get_entity).

        Returns:
            Any: Loaded graph object.

        Raises:
            DataNotFoundError: If graph data is not found.

        Note:
            Supports both legacy `key: str` API (deprecated) and new `**key_fields` API.
            The `key` parameter is maintained for backward compatibility but will be
            removed in a future version. Use `**key_fields` instead.
        """
        resolved_key = self._resolve_graph_key(key, key_fields)
        filepath = self.graph_dir / f"{entity_name}_{resolved_key}.pkl"
        if not filepath.exists():
            key_str = ", ".join(f"{k}={v!r}" for k, v in sorted(key_fields.items())) if key_fields else resolved_key
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"Graph data not found for '{entity_name}' with keys: {key_str}"
            )

        with filepath.open("rb") as f:
            return dill.load(f)

    def add_table_row(self, entity_name: str, row: Dict[str, Any]):
        """
        Insert a single row into an entity table.

        Args:
            entity_name (str): Name of the entity.
            row (dict): Row data.

        Returns:
            None
        """
        columns = ", ".join(row.keys())
        placeholders = ", ".join(["?" for _ in row])
        values = tuple(row.values())

        self.cursor.execute(
            f"INSERT INTO {entity_name} ({columns}) VALUES ({placeholders});",
            values,
        )
        self.conn.commit()

    def add_table_data(self, entity_name: str, data: List[Dict[str, Any]]):
        """
        Insert multiple rows into an entity table.

        Args:
            entity_name (str): Name of the entity.
            data (list of dict): Rows to insert.

        Returns:
            None
        """
        if not data:
            return

        columns = ", ".join(data[0].keys())
        placeholders = ", ".join(["?" for _ in data[0]])
        values = [tuple(row.values()) for row in data]

        self.cursor.executemany(
            f"INSERT INTO {entity_name} ({columns}) VALUES ({placeholders});",
            values,
        )
        self.conn.commit()

    def get_table_data(self, entity_name: str, **filters):
        """
        Retrieve table data as a DataFrame.

        Args:
            entity_name (str): Name of the entity.
            **filters: Column filters applied as equality comparisons.

        Returns:
            pd.DataFrame: Retrieved rows.
        """
        query = f"SELECT * FROM {entity_name}"
        params = None

        if filters:
            conditions = " AND ".join([f"{col} = ?" for col in filters])
            query += f" WHERE {conditions}"
            params = tuple(filters.values())

        df = pd.read_sql_query(query, self.conn, params=params)

        # Convert boolean fields
        model_cls = entity.SchemaMetadata.get_model(entity_name)
        if model_cls is not None:
            for field in entity.SchemaMetadata.get_fields(entity_name):
                if field.name in df.columns:
                    type_name, _, _ = resolve_field_type_and_nullable(model_cls, field)
                    if type_name == "boolean":
                        df[field.name] = df[field.name].astype(bool)

        return df

    def get_table_row(self, entity_name: str, **filters):
        """
        Retrieve a single row from an entity table.

        Args:
            entity_name (str): Name of the entity.
            **filters: Column filters.

        Returns:
            pd.Series: Row data.

        Raises:
            DataNotFoundError: If no matching row exists.
        """
        df = self.get_table_data(entity_name, **filters)
        if df.empty:
            raise DataNotFoundError(entity_name=entity_name)
        return df.iloc[0]

    def save_netlist(self, netlist, circuit: str, netlist_id: str, phase: str):
        """
        Store a netlist and its timing paths.

        Args:
            netlist: Netlist object.
            circuit (str): Circuit name.
            netlist_id (str): Netlist identifier.
            phase (str): Phase name.

        Returns:
            None
        """
        key = f"{circuit}-{netlist_id}-{phase}"
        timing_paths = netlist.timing_paths
        netlist.timing_paths = []

        self.add_graph_data("netlists", netlist, key)

        filepath = self.graph_dir / f"timing_paths_{key}.pkl"
        with filepath.open("wb") as f:
            dill.dump(timing_paths, f)

        netlist.timing_paths = timing_paths

    def load_netlist(self, circuit: str, netlist_id: str, phase: str, load_timing_paths: bool = True):
        """
        Load a stored netlist and optionally load its timing paths.

        Args:
            circuit (str): Circuit name.
            netlist_id (str): Netlist identifier.
            phase (str): Phase name.
            load_timing_paths (bool): Whether to load timing paths.

        Returns:
            Any: Loaded netlist object.

        Raises:
            DataNotFoundError: If the netlist or timing paths are missing.
        """
        key = f"{circuit}-{netlist_id}-{phase}"

        try:
            netlist_obj = self.get_graph_data("netlists", key)

            if load_timing_paths:
                filepath = self.graph_dir / f"timing_paths_{key}.pkl"
                with filepath.open("rb") as f:
                    netlist_obj.timing_paths = dill.load(f)

        except FileNotFoundError:
            raise DataNotFoundError(entity_name=key)

        return netlist_obj

    # ------------------------------------------------------------------
    # Image Storage
    # ------------------------------------------------------------------
    def _image_dir(self, entity_name: str) -> Path:
        """Get the directory where images for an entity are stored."""
        return self.data_dir / "images" / entity_name

    def add_image(self, entity_name: str, image_name: str, image: Image2D, **key_fields) -> None:
        """
        Store an Image2D associated with an entity row.

        Args:
            entity_name (str): Name of the entity.
            image_name (str): Name of the image field (e.g. "cell_placement").
            image (Image2D): The image to store.
            **key_fields: Primary key values identifying the row
                        (e.g. flow_id="X", stage="Y").

        Returns:
            None
        """
        # Ensure the image directory exists
        image_dir = self._image_dir(entity_name)
        image_dir.mkdir(parents=True, exist_ok=True)

        # Construct filename from field + primary keys
        key_str = "__".join(f"{k}={v}" for k, v in sorted(key_fields.items()))
        path = image_dir / f"{image_name}__{key_str}.npz"

        # Save as compressed numpy array
        np.savez_compressed(path, image)

    def get_image(self, entity_name: str, field: str, **key_fields) -> Image2D:
        """
        Retrieve an Image2D stored for a specific entity row.

        Args:
            entity_name (str): Name of the entity.
            field (str): Name of the stored image field.
            **key_fields: Primary key values identifying the row.

        Returns:
            Image2D: The loaded image.

        Raises:
            DataNotFoundError: If the image file does not exist.
        """
        # Construct expected path
        image_dir = self._image_dir(entity_name)
        key_str = "__".join(f"{k}={v}" for k, v in sorted(key_fields.items()))
        path = image_dir / f"{field}__{key_str}.npz"

        # Check if file exists
        if not path.exists():
            raise DataNotFoundError(entity_name=f"{entity_name}:{field}")

        # Load and return wrapped Image2D
        data = np.load(path)
        arr = data['arr_0']  # np.savez_compressed saves as 'arr_0'
        return Image2D(arr)
