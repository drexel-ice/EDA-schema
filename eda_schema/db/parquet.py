import json
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Optional
from collections.abc import Iterable

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc

from eda_schema import entity
from eda_schema.base import Image2D, resolve_field_type_and_nullable
from eda_schema.db.base import BaseDB
from eda_schema.errors import DataNotFoundError


def arrow_from_type(type_name: Optional[str]) -> Optional[pa.DataType]:
    """
    Convert a primitive type name into an Apache Arrow DataType.

    Args:
        type_name (str | None): Resolved primitive type name.

    Returns:
        pa.DataType | None: The corresponding Arrow type, or None if unsupported.
    """
    mapping = {
        "string": pa.string(),
        "number": pa.float64(),
        "integer": pa.int64(),
        "boolean": pa.bool_(),
    }
    return mapping.get(type_name)


@lru_cache(maxsize=None)
def build_arrow_schema(entity_name: str) -> pa.Schema:
    """
    Build an Apache Arrow schema for the given entity.

    Args:
        entity_name (str): Name of the entity.

    Returns:
        pa.Schema: Arrow schema describing the entity structure.
    """
    model_cls = entity.SchemaMetadata.get_model(entity_name)
    if model_cls is None:
        raise KeyError(f"Unknown entity: {entity_name}")

    entity_fields = entity.SchemaMetadata.get_fields(entity_name)
    if entity_fields is None:
        raise KeyError(f"No fields found for entity: {entity_name}")

    arrow_fields: list[pa.Field] = []

    for f in entity_fields:
        type_name, nullable, _ = resolve_field_type_and_nullable(model_cls, f)
        arrow_type = arrow_from_type(type_name)

        # Skip unsupported / non-tabular fields
        if arrow_type is None:
            continue

        arrow_fields.append(
            pa.field(
                f.name,
                arrow_type,
                nullable=nullable,
            )
        )

    return pa.schema(arrow_fields)


@lru_cache(maxsize=128)
def _load_arrow_table(path: Path) -> pa.Table:
    """
    Load an Arrow table from a Parquet file (cached).

    Args:
        path: Path to the Parquet file.

    Returns:
        pa.Table: Loaded Arrow table.
    """
    return pq.read_table(path)


class ParquetDB(BaseDB):
    """
    Parquet-backed storage for entities and graph data.
    """

    def __init__(self, data_home: str | Path):
        """
        Initialize the Parquet database.

        Args:
            data_home (str | Path): Root directory for all stored data.
        """
        self.data_home = Path(data_home)
        self._writers = {}  # entity_name -> ParquetWriter
        self._graph_writers = {}  # entity_name -> ParquetWriter

    def _entity_path(self, entity_name: str) -> Path:
        """
        Get the directory path for an entity.

        Args:
            entity_name (str): Name of the entity.

        Returns:
            Path: Directory where the entity's data is stored.
        """
        return self.data_home / entity_name

    def _table_path(self, entity_name: str) -> Path:
        """
        Get the path to an entity's Parquet table.

        Args:
            entity_name (str): Name of the entity.

        Returns:
            Path: Path to the Parquet file.
        """
        return self._entity_path(entity_name) / "table.parquet"

    def _image_dir(self, entity_name: str) -> Path:
        """
        Get the directory where image files for an entity are stored.

        Args:
            entity_name (str): Name of the entity.

        Returns:
            Path: Directory containing all image files associated with the entity.
        """
        return self._entity_path(entity_name) / "images"

    def _graph_path(self, entity_name: str) -> Path:
        """
        Get the directory where graph files are stored.

        Args:
            entity_name (str): Name of the entity.

        Returns:
            Path: Directory containing graph JSON files.
        """
        return self._entity_path(entity_name) / "graph.parquet"

    def _create_table(self, entity_name: str, is_graph_entity: bool):
        """
        Create an empty Parquet table for the entity.

        Args:
            entity_name (str): Name of the entity.
            is_graph_entity (bool): Whether the entity has graph data.
        """
        entity_dir = self._entity_path(entity_name)
        entity_dir.mkdir(parents=True, exist_ok=True)

        schema = build_arrow_schema(entity_name)
        empty_arrays = [pa.array([], type=field.type) for field in schema]
        empty_table = pa.Table.from_arrays(empty_arrays, schema=schema)
        pq.write_table(empty_table, self._table_path(entity_name))

        # Create empty graph.parquet if needed
        if is_graph_entity:
            pk_cols = entity.SchemaMetadata.get_pk_columns(entity_name)
            if not pk_cols:
                raise ValueError(f"Entity '{entity_name}' must define at least one primary key")

            model_cls = entity.SchemaMetadata.get_model(entity_name)
            model_fields = entity.SchemaMetadata.get_fields(entity_name)
            field_map = {f.name: f for f in model_fields}

            graph_fields: list[pa.Field] = []

            for pk in pk_cols:
                field = field_map[pk]
                type_name, _, _ = resolve_field_type_and_nullable(model_cls, field)
                arrow_type = arrow_from_type(type_name) or pa.string()

                # Primary keys are never nullable
                graph_fields.append(pa.field(pk, arrow_type, nullable=False))

            # Serialized graph payload
            graph_fields.append(pa.field("graph_json", pa.string(), nullable=False))

            gschema = pa.schema(graph_fields)

            empty_arrays = [pa.array([], type=field.type) for field in graph_fields]
            empty_graph_table = pa.Table.from_arrays(empty_arrays, schema=gschema)

            pq.write_table(empty_graph_table, self._graph_path(entity_name))


    def create_dataset_tables(self):
        """
        Create Parquet tables for all registered entities.

        Returns:
            None
        """
        self.data_home.mkdir(parents=True, exist_ok=True)

        for entity_name, _ in entity.SchemaMetadata.items():
            self._create_table(
                entity_name=entity_name,
                is_graph_entity=entity.SchemaMetadata.is_graph_entity(entity_name),
            )

    def _append_to_table(self, entity_name: str, df: pd.DataFrame):
        """
        Append DataFrame rows to the entity table.

        Args:
            entity_name (str): Name of the entity.
            df (pd.DataFrame): Rows to append.
        
        Returns:
            None
        """
        if df.empty:
            return

        table_path = self._table_path(entity_name)
        schema = build_arrow_schema(entity_name)
        table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)

        writer = self._writers.get(entity_name)
        if writer is None:
            writer = pq.ParquetWriter(table_path, schema)
            self._writers[entity_name] = writer

        writer.write_table(table)

    def add_table_row(self, entity_name: str, row: Dict[str, Any]):
        """
        Add a single row to the entity table.

        Args:
            entity_name (str): Name of the entity.
            row (dict): Row data.
        """
        self._append_to_table(entity_name, pd.DataFrame([row]))

    def add_table_data(self, entity_name: str, data: List[Dict[str, Any]]):
        """
        Add multiple rows to the entity table.

        Args:
            entity_name (str): Name of the entity.
            data (list): List of row dictionaries.
        """
        if data:
            self._append_to_table(entity_name, pd.DataFrame(data))

    def get_table_data(self, entity_name: str, **filters) -> pd.DataFrame:
        """
        Retrieve table data for an entity, optionally filtered.

        Args:
            entity_name (str): Name of the entity.
            **filters: Column filters.

        Returns:
            pd.DataFrame: Filtered table data.

        Raises:
            FileNotFoundError: If the table file does not exist.
            DataNotFoundError: If the entity is not found.
        """
        # Ensure writers are closed before reading to prevent corruption errors
        self._ensure_writers_closed()

        table_path = self._table_path(entity_name)
        if not table_path.exists():
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"Table file not found: {table_path}. "
                       f"Did you call create_dataset_tables() first?"
            )

        try:
            table = _load_arrow_table(table_path)
        except Exception as e:
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"Failed to read table from {table_path}: {e}. "
                       f"This may occur if writers weren't closed before reading. "
                       f"Use 'with ParquetDB(...) as db:' or call db.close() after writes."
            ) from e

        if filters:
            mask = None

            for key, value in filters.items():
                col = table[key]
                col_type = col.type

                # -------------------------
                # Iterable (IN filter)
                # -------------------------
                if (
                    isinstance(value, Iterable)
                    and not isinstance(value, (str, bytes))
                ):
                    values = list(value)

                    # Empty IN → no rows
                    if not values:
                        return table.slice(0, 0).to_pandas()

                    value_array = pa.array(values, type=col_type)
                    cond = pc.is_in(col, value_set=value_array)

                # -------------------------
                # Scalar (= filter)
                # -------------------------
                else:
                    scalar = pa.scalar(value, type=col_type)
                    cond = pc.equal(col, scalar)

                mask = cond if mask is None else pc.and_(mask, cond)

            table = table.filter(mask)

        return table.to_pandas()

    def get_table_row(self, entity_name: str, **filters) -> pd.Series:
        """
        Retrieve a single row matching filters.

        Args:
            entity_name (str): Name of the entity.
            **filters: Column filters.

        Returns:
            pd.Series: Matching row.

        Raises:
            DataNotFoundError: If no row matches the filters or entity not found.
        """
        df = self.get_table_data(entity_name, **filters)
        if df.empty:
            filter_str = ", ".join(f"{k}={v!r}" for k, v in filters.items())
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"No row found matching filters: {filter_str}"
            )
        return df.iloc[0]

    # --------------------------------------------------------------
    # Internal helpers (DB responsibility only)
    # --------------------------------------------------------------
    def _validate_graph_keys(
        self,
        entity_name: str,
        key_fields: Dict[str, Any],
    ) -> List[str]:
        """
        Validate that provided key fields exactly match the entity's
        primary-key definition.

        Args:
            entity_name (str): Graph entity name.
            key_fields (dict): Provided primary-key values.

        Returns:
            list[str]: Ordered list of primary-key column names.

        Raises:
            ValueError: If required primary-key fields are missing
                        or unexpected fields are provided.
        """
        pk_cols = entity.SchemaMetadata.get_pk_columns(entity_name)

        provided = set(key_fields.keys())
        required = set(pk_cols)

        missing = required - provided
        extra = provided - required

        if missing:
            raise ValueError(
                f"Missing primary-key fields for '{entity_name}': {sorted(missing)}"
            )

        if extra:
            raise ValueError(
                f"Unexpected key fields for '{entity_name}': {sorted(extra)} "
                f"(expected {sorted(pk_cols)})"
            )

        return pk_cols

    def _build_graph_row(
        self,
        entity_name: str,
        graph_data: Dict[str, Any],
        key_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build a single graph-table row from graph data and primary-key fields.

        Performs primary-key validation and JSON serialization of the graph.

        Args:
            entity_name (str): Graph entity name.
            graph_data (dict): Graph structure (JSON-serializable).
            key_fields (dict): Primary-key values.

        Returns:
            dict: Row dictionary matching the graph.parquet schema.
        """
        pk_cols = self._validate_graph_keys(entity_name, key_fields)

        row = {pk: str(key_fields[pk]) for pk in pk_cols}
        row["graph_json"] = json.dumps(graph_data)

        return row

    def _write_graph_rows(
        self,
        entity_name: str,
        rows: List[Dict[str, Any]],
    ):
        """
        Append one or more graph rows to the entity's graph Parquet file.

        Manages ParquetWriter lifecycle and ensures schema consistency.

        Args:
            entity_name (str): Graph entity name.
            rows (list): List of fully-built graph rows.
        """
        if not rows:
            return

        gpath = self._graph_path(entity_name)

        writer = self._graph_writers.get(entity_name)
        if writer is None:
            schema = pq.read_schema(gpath)
            writer = pq.ParquetWriter(gpath, schema)
            self._graph_writers[entity_name] = writer

        table = pa.Table.from_pylist(rows, schema=writer.schema)
        writer.write_table(table)

    def add_graph_data_batch(
        self,
        entity_name: str,
        rows: List[Dict[str, Any]],
    ):
        """
        Add multiple graph entries in a single Parquet write.

        Each input row must have the form:
            {
                "data": <graph_dict>,
                "<pk1>": value,
                "<pk2>": value,
                ...
            }

        Args:
            entity_name (str): Graph entity name.
            rows (list): List of graph row dictionaries.
        """
        if not rows:
            return

        built_rows = []
        for row in rows:
            if "data" not in row:
                raise ValueError("Graph row must contain a 'data' field")

            graph_data = row["data"]
            key_fields = {k: v for k, v in row.items() if k != "data"}

            built_rows.append(
                self._build_graph_row(entity_name, graph_data, key_fields)
            )

        self._write_graph_rows(entity_name, built_rows)

    def add_graph_data(
        self,
        entity_name: str,
        graph_data: Dict[str, Any],
        **key_fields,
    ):
        """
        Add a single graph entry for an entity.

        Args:
            entity_name (str): Graph entity name.
            graph_data (dict): Graph structure (JSON-serializable).
            **key_fields: Primary-key values identifying the row.
        """
        row = self._build_graph_row(entity_name, graph_data, key_fields)
        self._write_graph_rows(entity_name, [row])

    def get_graph_data(self, entity_name: str, **key_fields) -> Dict[str, Any]:
        """
        Retrieve graph_json from graph.parquet using primary-key values.

        Args:
            entity_name (str): Entity type.
            **key_fields: Primary-key values (must include all PK columns).

        Returns:
            dict: Decoded graph dictionary.

        Raises:
            ValueError: If PKs are missing.
            DataNotFoundError: If the graph data is not found.
        """
        # Ensure writers are closed before reading
        self._ensure_writers_closed()

        graph_path = self._graph_path(entity_name)
        if not graph_path.exists():
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"Graph file not found: {graph_path}. "
                       f"Did you call create_dataset_tables() and add graph data?"
            )

        pk_cols = entity.SchemaMetadata.get_pk_columns(entity_name)
        if not pk_cols:
            raise ValueError(
                f"Entity '{entity_name}' has no defined primary-key fields. "
                f"Cannot retrieve graph data without primary keys."
            )

        missing = [pk for pk in pk_cols if pk not in key_fields]
        if missing:
            raise ValueError(
                f"Missing primary-key fields for '{entity_name}': {missing}. "
                f"Required: {pk_cols}. Provided: {list(key_fields.keys())}"
            )

        try:
            table = _load_arrow_table(graph_path)
        except Exception as e:
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"Failed to read graph data from {graph_path}: {e}. "
                       f"This may occur if writers weren't closed before reading. "
                       f"Use 'with ParquetDB(...) as db:' or call db.close() after writes."
            ) from e

        mask = None
        for pk in pk_cols:
            cond = pc.equal(table[pk], pa.scalar(str(key_fields[pk])))
            mask = cond if mask is None else pc.and_(mask, cond)

        filtered = table.filter(mask)

        if filtered.num_rows == 0:
            key_str = ", ".join(f"{k}={v!r}" for k, v in key_fields.items())
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"No graph data found for '{entity_name}' with keys: {key_str}"
            )

        return json.loads(filtered["graph_json"][0].as_py())

    def add_image(self, entity_name: str, image_name: str, image: Image2D, **key_fields):
        """
        Store an image (NumPy array) associated with an entity row.

        Args:
            entity_name (str): Name of the entity.
            image_name (str): Name of the image field (e.g. "cell_placement").
            image (Image2D): Image data.
            **key_fields: Primary-key values identifying the row
                        (e.g. flow_id="X", stage="Y").

        Returns:
            str: Filesystem path where the image was stored.
        """
        # Ensure the image directory exists
        image_dir = self._image_dir(entity_name)
        image_dir.mkdir(parents=True, exist_ok=True)

        # Construct filename from field + primary keys
        key_str = "__".join(f"{k}={v}" for k, v in key_fields.items())
        path = image_dir / f"{image_name}__{key_str}"

        # Save as .npy
        np.savez_compressed(path, image)

        return str(path)

    def get_image(self, entity_name: str, image_name: str, **key_fields) -> Image2D:
        """
        Retrieve an image associated with an entity row.

        Args:
            entity_name (str): Name of the entity.
            image_name (str): Name of the image field.
            **key_fields: Primary-key values identifying the row.

        Returns:
            Image2D: The loaded image.

        Raises:
            DataNotFoundError: If the image file does not exist.
        """
        # --------------------------------------------------------------
        # Construct expected path
        # --------------------------------------------------------------
        image_dir = self._image_dir(entity_name)
        key_str = "__".join(f"{k}={v}" for k, v in key_fields.items())
        path = image_dir / f"{image_name}__{key_str}.npz"

        # --------------------------------------------------------------
        # Ensure the file exists
        # --------------------------------------------------------------
        if not path.exists():
            key_str = ", ".join(f"{k}={v!r}" for k, v in key_fields.items())
            raise DataNotFoundError(
                entity_name=f"{entity_name}:{image_name}",
                message=f"Image '{image_name}' not found for entity '{entity_name}' "
                       f"with keys: {key_str}. Expected path: {path}"
            )

        # --------------------------------------------------------------
        # Load and return wrapped Image2D
        # --------------------------------------------------------------
        data = np.load(path)
        arr = data['arr_0']
        return entity.Image2D(arr)

    def close(self):
        """
        Close all active Parquet writers and release file handles.

        This method should be called after all write operations are complete
        to ensure data is flushed to disk. Alternatively, use the context manager:

        ```python
        with ParquetDB(data_home) as db:
            # All operations here
            # Writers are automatically closed on exit
        ```
        """
        for entity_name, writer in list(self._writers.items()):
            try:
                writer.close()
            except Exception as e:
                # Log but don't fail - try to close remaining writers
                import warnings
                warnings.warn(
                    f"Error closing writer for entity '{entity_name}': {e}",
                    RuntimeWarning
                )

        for entity_name, writer in list(self._graph_writers.items()):
            try:
                writer.close()
            except Exception as e:
                import warnings
                warnings.warn(
                    f"Error closing graph writer for entity '{entity_name}': {e}",
                    RuntimeWarning
                )

        self._writers.clear()
        self._graph_writers.clear()

    def __enter__(self):
        """
        Context manager entry.

        Returns:
            ParquetDB: Self instance for use in 'with' statements.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - automatically closes all writers.

        Args:
            exc_type: Exception type (if any).
            exc_val: Exception value (if any).
            exc_tb: Exception traceback (if any).

        Returns:
            bool: False to propagate exceptions, True to suppress them.
        """
        self.close()
        return False

    def _ensure_writers_closed(self):
        """
        Internal method to ensure writers are closed before read operations.

        This is called automatically before read operations to prevent
        "Parquet magic bytes not found" errors.
        """
        if self._writers or self._graph_writers:
            self.close()
