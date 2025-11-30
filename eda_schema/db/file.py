from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from eda_schema.db.base import BaseDB
from eda_schema import entity


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
        """Return the directory for an entity."""
        return self.data_home / entity_name

    def _table_path(self, entity_name: str) -> Path:
        """Return the CSV table path for an entity."""
        return self._entity_dir(entity_name) / "table.csv"

    def _graph_dir(self, entity_name: str) -> Path:
        """Return the graph storage directory for an entity."""
        return self._entity_dir(entity_name) / "graphs"

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------
    def _create_table(self, entity_name: str, columns: List[str], is_graph_entity: bool):
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
        for entity_name, schema in entity.SchemaMetadata.items():
            columns = list(schema.keys())
            is_graph = entity.SchemaMetadata.is_graph_entity(entity_name)

            self._create_table(
                entity_name=entity_name,
                columns=columns,
                is_graph_entity=is_graph,
            )

    # ------------------------------------------------------------------
    # Graph Operations
    # ------------------------------------------------------------------
    def add_graph_data(self, entity_name: str, graph: Any, key: str):
        """
        Add graph data to the database.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object containing the data (must define graph_dict()).
            key (str): Unique identifier for the graph data.
        """
        key = key.replace("/", "_")
        graph_path = self._graph_dir(entity_name)
        graph_path.mkdir(exist_ok=True)

        out_path = graph_path / f"{key}.json"
        with out_path.open("w") as f:
            json.dump(graph.graph_dict(), f)

    def get_graph_data(self, entity_name: str, key: str) -> Dict[str, Any]:
        """
        Retrieve graph data from the database.

        Args:
            entity_name (str): Name of the entity.
            key (str): Unique identifier for the graph data.

        Returns:
            dict: Graph data dictionary.
        """
        key = key.replace("/", "_")
        graph_file = self._graph_dir(entity_name) / f"{key}.json"
        if not graph_file.exists():
            raise FileNotFoundError(f"Graph not found: {graph_file}")

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
        df = pd.DataFrame([row])
        df.to_csv(
            self._table_path(entity_name),
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
