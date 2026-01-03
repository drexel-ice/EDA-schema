from pathlib import Path
import sqlite3
import dill
from typing import Any, Dict, List, Optional

import pandas as pd

from eda_schema import entity
from eda_schema.db.base import BaseDB
from eda_schema.errors import DataNotFoundError
from eda_schema.base import resolve_field_type_and_nullable


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
        for entity_name, model in entity.SchemaMetadata.items():
            columns = []
            for field in entity.SchemaMetadata.get_fields(entity_name):
                type_name, is_nullable, _ = resolve_field_type_and_nullable(field)
                sqlite_type = sqlite_type_from_type(type_name)
                if sqlite_type is None:
                    continue
                null_constraint = "NULL" if is_nullable else "NOT NULL"
                columns.append(f"{f.name} {sqlite_type} {null_constraint}")

            if not columns:
                continue

            column_defs = ", ".join(columns)
            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {entity_name} ({column_defs});"
            )

        self.conn.commit()

    def add_graph_data(self, entity_name: str, graph: Any, key: str):
        """
        Store graph data as a pickle file.

        Args:
            entity_name (str): Name of the entity.
            graph (Any): Graph object to store.
            key (str): Unique graph identifier.

        Returns:
            None
        """
        filepath = self.graph_dir / f"{entity_name}_{key}.pkl"
        with filepath.open("wb") as f:
            dill.dump(graph, f)

    def get_graph_data(self, entity_name: str, key: str):
        """
        Load stored graph data.

        Args:
            entity_name (str): Name of the entity.
            key (str): Unique graph identifier.

        Returns:
            Any: Loaded graph object.
        """
        filepath = self.graph_dir / f"{entity_name}_{key}.pkl"
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
        schema_meta = entity.SchemaMetadata.get_schema(entity_name)
        for col in df.columns:
            field_meta = schema_meta.get(col, {})
            type_name = field_meta.get("type")

            if type_name == "boolean" or (isinstance(type_name, list) and "boolean" in type_name):
                df[col] = df[col].astype(bool)

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
