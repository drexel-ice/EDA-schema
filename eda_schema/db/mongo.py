import pandas as pd
from pymongo import MongoClient

from eda_schema import entity
from eda_schema.db.base import BaseDB


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

    def add_graph_data(self, entity_name: str, graph, key: str):
        """
        Store graph data for an entity.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object with a graph_dict() method.
            key (str): Unique graph identifier.

        Returns:
            None
        """
        self.db[f"{entity_name}_graph"].insert_one({
            "key": key,
            **graph.graph_dict()
        })

    def get_graph_data(self, entity_name: str, key: str):
        """
        Retrieve graph data for an entity.

        Args:
            entity_name (str): Name of the entity.
            key (str): Unique graph identifier.

        Returns:
            dict | None: Graph data dictionary if found, else None.
        """
        return self.db[f"{entity_name}_graph"].find_one({"key": key})

    def add_table_row(self, entity_name: str, row: dict):
        """
        Insert a single row into an entity table.

        Args:
            entity_name (str): Name of the entity.
            row (dict): Row data.

        Returns:
            None
        """
        self.db[f"{entity_name}_tabular"].insert_one(row)

    def add_table_data(self, entity_name: str, data: list):
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
