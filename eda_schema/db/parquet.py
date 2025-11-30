import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from eda_schema import entity
from eda_schema.base import resolve_schema_type_and_nullable
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


def build_arrow_schema(entity_name: str) -> pa.Schema:
    """
    Build an Apache Arrow schema for the given entity.

    Args:
        entity_name (str): Name of the entity.

    Returns:
        pa.Schema: Arrow schema describing the entity structure.
    """
    raw = entity.SchemaMetadata.get_schema(entity_name)
    fields = []

    for col_name, col_info in raw.items():
        type_name, nullable, _ = resolve_schema_type_and_nullable(col_info)
        arrow_type = arrow_from_type(type_name)

        if arrow_type:
            fields.append(pa.field(col_name, arrow_type, nullable=nullable))

    return pa.schema(fields)


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

    def _graph_path(self, entity_name: str) -> Path:
        """
        Get the directory where graph files are stored.

        Args:
            entity_name (str): Name of the entity.

        Returns:
            Path: Directory containing graph JSON files.
        """
        return self._entity_path(entity_name) / "graph.parquet"

    def _create_table(self, entity_name: str, columns: List[str], is_graph_entity: bool):
        """
        Create an empty Parquet table for the entity.

        Args:
            entity_name (str): Name of the entity.
            columns (list): Unused; present for compatibility.
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
            schema_dict = entity.SchemaMetadata.get_schema(entity_name)
            pk_cols = entity.SchemaMetadata.get_pk_columns(entity_name)

            if not pk_cols:
                raise ValueError(f"Entity '{entity_name}' must define at least one primary key")

            fields = []
            for pk in pk_cols:
                type_name, nullable, _ = resolve_schema_type_and_nullable(schema_dict[pk])
                arrow_type = arrow_from_type(type_name)

                # PKs must never be nullable
                fields.append(pa.field(pk, arrow_type or pa.string(), nullable=False))

            # graph_json is required
            fields.append(pa.field("graph_json", pa.string(), nullable=False))

            gschema = pa.schema(fields)

            empty_arrays = [pa.array([], type=f.type) for f in fields]
            empty_graph_table = pa.Table.from_arrays(empty_arrays, schema=gschema)

            pq.write_table(empty_graph_table, self._graph_path(entity_name))


    def create_dataset_tables(self):
        """
        Create Parquet tables for all registered entities.

        Returns:
            None
        """
        self.data_home.mkdir(parents=True, exist_ok=True)

        for entity_name, schema in entity.SchemaMetadata.items():
            self._create_table(
                entity_name,
                list(schema.keys()),
                entity.SchemaMetadata.is_graph_entity(entity_name),
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
        table_path = self._table_path(entity_name)
        existing = pq.read_table(table_path)

        schema = build_arrow_schema(entity_name)
        append_table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        combined = pa.concat_tables([existing, append_table])

        pq.write_table(combined, table_path)

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
        """
        df = pd.read_parquet(self._table_path(entity_name))

        for key, value in filters.items():
            df = df[df[key] == value]

        return df

    def get_table_row(self, entity_name: str, **filters) -> pd.Series:
        """
        Retrieve a single row matching filters.

        Args:
            entity_name (str): Name of the entity.
            **filters: Column filters.

        Returns:
            pd.Series: Matching row.

        Raises:
            DataNotFoundError: If no row matches the filters.
        """
        df = self.get_table_data(entity_name, **filters)
        if df.empty:
            raise DataNotFoundError(entity_name=entity_name)
        return df.iloc[0]

    def add_graph_data(self, entity_name: str, graph: Any, **key_fields):
        """
        Append a new graph row into graph.parquet for the entity.

        Args:
            entity_name (str): Entity type.
            graph (GraphEntity): Object exposing graph_dict().
            **key_fields: Primary-key values (e.g. flow_id="X", stage="Y").
        """
        # --------------------------------------------------------------
        # Validate primary-key fields
        # --------------------------------------------------------------
        pk_cols = entity.SchemaMetadata.get_pk_columns(entity_name)
        provided = set(key_fields.keys())
        required = set(pk_cols)

        missing = required - provided
        extra   = provided - required

        if missing:
            raise ValueError(
                f"Missing primary-key fields for '{entity_name}': {sorted(missing)}"
            )

        if extra:
            raise ValueError(
                f"Unexpected key fields for '{entity_name}': {sorted(extra)} "
                f"(expected {sorted(pk_cols)})"
            )

        # --------------------------------------------------------------
        # Build row dictionary for Parquet
        # --------------------------------------------------------------
        row_dict = {pk: [str(key_fields[pk])] for pk in pk_cols}
        row_dict["graph_json"] = [json.dumps(graph.graph_dict())]

        # --------------------------------------------------------------
        # Load → append → save
        # --------------------------------------------------------------
        gpath = self._graph_path(entity_name)
        existing = pq.read_table(gpath)

        new_table = pa.Table.from_pydict(row_dict, schema=existing.schema)

        combined = pa.concat_tables([existing, new_table])
        pq.write_table(combined, gpath)

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
            DataNotFoundError: If no matching graph row exists.
        """
        df = pq.read_table(self._graph_path(entity_name)).to_pandas()

        pk_cols = entity.SchemaMetadata.get_pk_columns(entity_name)

        # Validate PK completeness
        missing = [pk for pk in pk_cols if pk not in key_fields]
        if missing:
            raise ValueError(
                f"Missing primary-key fields for '{entity_name}': {missing}"
            )

        # Filter on all PK fields
        for pk in pk_cols:
            df = df[df[pk] == str(key_fields[pk])]

        if df.empty:
            raise DataNotFoundError(
                entity_name=f"{entity_name} (graph key={key_fields})"
            )

        return json.loads(df.iloc[0]["graph_json"])
