from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from eda_schema import entity
from eda_schema.base import Image2D
from eda_schema.db.base import BaseDB
from eda_schema.errors import DataNotFoundError


class FileDB(BaseDB):
    """
    File-based backend for storing EDA-schema data tables and graph data.

    This database stores:
        - One CSV table per entity
        - Graphs as JSON files under <entity>/graphs/

    Attributes:
        data_home (Path): Root directory where all entity folders are stored.
    """

    def __init__(self, data_home: str | Path):
        """
        Initialize the file-backed database.

        Args:
            data_home (str | Path): Root directory for all stored data.
        """
        self.data_home = Path(data_home)
        self.data_home.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _entity_dir(self, entity_name: str) -> Path:
        """
        Get the directory path for an entity.

        Args:
            entity_name: Name of the entity.

        Returns:
            Path: Directory where the entity's data is stored.
        """
        return self.data_home / entity_name

    def _table_path(self, entity_name: str) -> Path:
        """
        Get the CSV table path for an entity.

        Args:
            entity_name: Name of the entity.

        Returns:
            Path: Path to the CSV file for the entity's table data.
        """
        return self._entity_dir(entity_name) / "table.csv"

    def _graph_dir(self, entity_name: str) -> Path:
        """
        Get the graph storage directory for an entity.

        Args:
            entity_name: Name of the entity.

        Returns:
            Path: Directory containing graph JSON files for the entity.
        """
        return self._entity_dir(entity_name) / "graphs"

    def _image_dir(self, entity_name: str) -> Path:
        """
        Get the image storage directory for an entity.

        Args:
            entity_name: Name of the entity.

        Returns:
            Path: Directory containing image NPZ files for the entity.
        """
        return self._entity_dir(entity_name) / "images"

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------
    def _create_table(
        self, entity_name: str, columns: List[str], is_graph_entity: bool
    ):
        """
        Create the directory + table for an entity.

        Args:
            entity_name (str): Name of the entity.
            columns (list[str]): Column names for the table.
            is_graph_entity (bool): Whether the entity contains graphs.
        """
        dir_path = self._entity_dir(entity_name)
        dir_path.mkdir(parents=True, exist_ok=True)

        if is_graph_entity:
            self._graph_dir(entity_name).mkdir(exist_ok=True)

        # Create empty table
        df = pd.DataFrame(columns=columns)
        df.to_csv(self._table_path(entity_name), index=False)

    def create_dataset_tables(self):
        """
        Create tables for all entities defined in SchemaMetadata.
        """
        for entity_name, model_cls in entity.SchemaMetadata.items():
            columns = entity.SchemaMetadata.get_columns(entity_name)
            is_graph = entity.SchemaMetadata.is_graph_entity(entity_name)

            self._create_table(
                entity_name=entity_name,
                columns=columns,
                is_graph_entity=is_graph,
            )

    # ------------------------------------------------------------------
    # Graph Operations
    # ------------------------------------------------------------------
    def add_graph_data(
        self, entity_name: str, graph: Any, key: str = None, **key_fields
    ) -> None:
        """
        Add graph data to the database.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object containing the data (must define graph_dict()).
            key (str, optional): Unique identifier for the graph data (legacy API, deprecated).
            **key_fields: Primary key values (preferred API).

        Returns:
            None

        Note:
            Supports both legacy `key: str` API (deprecated) and new `**key_fields` API.
            The `key` parameter is maintained for backward compatibility but will be
            removed in a future version. Use `**key_fields` instead.
        """
        resolved_key = self._resolve_graph_key(key, key_fields).replace("/", "_")
        graph_path = self._graph_dir(entity_name)
        graph_path.mkdir(exist_ok=True)

        out_path = graph_path / f"{resolved_key}.json"
        # Handle both dict and object with graph_dict() method
        if isinstance(graph, dict):
            graph_data = graph
        elif hasattr(graph, "graph_dict"):
            graph_data = graph.graph_dict()
        else:
            raise TypeError(
                f"Graph must be a dict or an object with graph_dict() method, "
                f"got {type(graph)}"
            )
        with out_path.open("w") as f:
            json.dump(graph_data, f)

    def get_graph_data(
        self, entity_name: str, key: str = None, **key_fields
    ) -> Dict[str, Any]:
        """
        Retrieve graph data from the database.

        Args:
            entity_name (str): Name of the entity.
            key (str, optional): Unique identifier for the graph data (legacy API, deprecated).
            **key_fields: Primary key values (preferred API, used by BaseDB.get_entity).

        Returns:
            dict: Graph data dictionary.

        Raises:
            DataNotFoundError: If graph data is not found.

        Note:
            Supports both legacy `key: str` API (deprecated) and new `**key_fields` API.
            The `key` parameter is maintained for backward compatibility but will be
            removed in a future version. Use `**key_fields` instead.
        """
        resolved_key = self._resolve_graph_key(key, key_fields).replace("/", "_")
        graph_file = self._graph_dir(entity_name) / f"{resolved_key}.json"
        if not graph_file.exists():
            key_str = (
                ", ".join(f"{k}={v!r}" for k, v in sorted(key_fields.items()))
                if key_fields
                else resolved_key
            )
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"Graph data not found for '{entity_name}' with keys: {key_str}",
            )

        with graph_file.open() as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Table Operations
    # ------------------------------------------------------------------
    def add_table_row(self, entity_name: str, row: Dict[str, Any]):
        """
        Append a single row to an entity table.

        Args:
            entity_name (str): Name of the entity.
            row (dict): The row to append.
        """
        table_path = self._table_path(entity_name)

        # Read existing table to get column order
        if table_path.exists():
            existing_df = pd.read_csv(table_path)
            columns = existing_df.columns.tolist()
        else:
            # If table doesn't exist, use columns from schema
            columns = entity.SchemaMetadata.get_columns(entity_name)

        # Create DataFrame with correct column order
        row_ordered = {col: row.get(col) for col in columns}
        df = pd.DataFrame([row_ordered])

        df.to_csv(
            table_path,
            mode="a",
            index=False,
            header=False,
        )

    def add_table_data(self, entity_name: str, data: List[Dict[str, Any]]):
        """
        Append multiple rows to an entity table.

        Args:
            entity_name (str): Name of the entity.
            data (list): Rows to insert.
        """
        df = pd.DataFrame(data)
        df.to_csv(
            self._table_path(entity_name),
            mode="a",
            index=False,
            header=False,
        )

    def get_table_data(self, entity_name: str, **filters: Any) -> pd.DataFrame:
        """
        Retrieve rows from a data table.

        Args:
            entity_name (str): Table to query.
            **filters: Column=value filters.

        Returns:
            pd.DataFrame: Filtered results.
        """
        table_path = self._table_path(entity_name)
        if not table_path.exists():
            raise FileNotFoundError(f"No table found for entity: {entity_name}")

        df = pd.read_csv(table_path)

        for col, val in filters.items():
            if col not in df.columns:
                raise KeyError(f"Column '{col}' not found in '{entity_name}' table.")
            df = df[df[col] == val]

        return df

    def get_table_row(self, entity_name: str, **filters: Any) -> pd.Series:
        """
        Retrieve one row matching filter conditions.

        Args:
            entity_name (str): Table to query.
            **filters: Column=value filters (must match exactly one row).

        Returns:
            pd.Series: The matched row.
        """
        df = self.get_table_data(entity_name, **filters)

        if df.empty:
            raise ValueError(f"No rows match filters: {filters}")

        return df.iloc[0]

    # ------------------------------------------------------------------
    # Image Storage
    # ------------------------------------------------------------------
    def add_image(
        self, entity_name: str, image_name: str, image: Image2D, **key_fields
    ) -> None:
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
        arr = data["arr_0"]  # np.savez_compressed saves as 'arr_0'
        return Image2D(arr)
