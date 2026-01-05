from typing import Any, Dict, List

import pandas as pd
from pymongo import MongoClient

from eda_schema import entity
from eda_schema.db.base import BaseDB
from eda_schema.errors import DataNotFoundError


class MongoDB(BaseDB, MongoClient):
    """
    MongoDB-backed database for storing entity tables and graph data.
    """

    def __init__(self, db_uri: str, db_name: str):
        """
        Initialize the MongoDB connection.

        Args:
            db_uri (str): MongoDB connection URI.
            db_name (str): Database name to use.
        """
        self.db_uri = db_uri
        self.db_name = db_name
        super().__init__(self.db_uri)
        self.db = self[self.db_name]


    def create_dataset_tables(self):
        """
        Initialize collections for all entities and store metadata.

        Returns:
            None
        """
        self.drop_database(self.db_name)

        metadata = []
        for entity_name, schema in entity.SchemaMetadata.items():
            metadata.append({
                "entity": entity_name,
                "columns": list(schema.keys())
            })

        self.db["metadata"].insert_many(metadata)

    def add_graph_data(self, entity_name: str, graph: Any, key: str = None, **key_fields) -> None:
        """
        Store graph data for an entity.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object with a graph_dict() method or dict.
            key (str, optional): Unique graph identifier (legacy API, deprecated).
            **key_fields: Primary key values (preferred API).

        Returns:
            None

        Note:
            Supports both legacy `key: str` API (deprecated) and new `**key_fields` API.
            The `key` parameter is maintained for backward compatibility but will be
            removed in a future version. Use `**key_fields` instead.
        """
        resolved_key = self._resolve_graph_key(key, key_fields)

        # Handle both dict and object with graph_dict() method
        if isinstance(graph, dict):
            graph_data = graph
        elif hasattr(graph, 'graph_dict'):
            graph_data = graph.graph_dict()
        else:
            raise TypeError(
                f"Graph must be a dict or an object with graph_dict() method, "
                f"got {type(graph)}"
            )

        self.db[f"{entity_name}_graph"].insert_one({
            "key": resolved_key,
            **graph_data
        })

    def get_graph_data(self, entity_name: str, key: str = None, **key_fields) -> Dict[str, Any]:
        """
        Retrieve graph data for an entity.

        Args:
            entity_name (str): Name of the entity.
            key (str, optional): Unique graph identifier (legacy API, deprecated).
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
        resolved_key = self._resolve_graph_key(key, key_fields)
        result = self.db[f"{entity_name}_graph"].find_one({"key": resolved_key})
        if result is None:
            key_str = ", ".join(f"{k}={v!r}" for k, v in sorted(key_fields.items())) if key_fields else resolved_key
            raise DataNotFoundError(
                entity_name=entity_name,
                message=f"Graph data not found for '{entity_name}' with keys: {key_str}"
            )
        return result

    def add_table_row(self, entity_name: str, row: Dict[str, Any]) -> None:
        """
        Insert a single row into an entity table.

        Args:
            entity_name (str): Name of the entity.
            row (dict): Row data.

        Returns:
            None
        """
        self.db[f"{entity_name}_tabular"].insert_one(row)

    def add_table_data(self, entity_name: str, data: List[Dict[str, Any]]) -> None:
        """
        Insert multiple rows into an entity table.

        Args:
            entity_name (str): Name of the entity.
            data (list of dict): List of rows to insert.

        Returns:
            None
        """
        self.db[f"{entity_name}_tabular"].insert_many(data)

    def get_table_data(self, entity_name: str, **filters) -> pd.DataFrame:
        """
        Retrieve all matching rows from an entity table.

        Args:
            entity_name (str): Name of the entity.
            **filters: Column filters applied as equality matches.

        Returns:
            pd.DataFrame: Data rows as a DataFrame.
        """
        rows = list(self.db[f"{entity_name}_tabular"].find(filters))

        # Remove MongoDB internal ID
        for row in rows:
            row.pop("_id", None)

        # Load column ordering from metadata
        metadata = self.db["metadata"].find_one({"entity": entity_name})
        columns = metadata["columns"]

        return pd.DataFrame(rows, columns=columns)

    def get_table_row(self, entity_name: str, **filters) -> pd.Series:
        """
        Retrieve a single matching row from an entity table.

        Args:
            entity_name (str): Name of the entity.
            **filters: Column filters.

        Returns:
            pd.Series: Row data, or an empty Series if not found.
        """
        row = self.db[f"{entity_name}_tabular"].find_one(filters)

        if not row:
            return pd.Series()

        row.pop("_id", None)
        return pd.Series(row)
