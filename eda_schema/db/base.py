from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd

from eda_schema import entity


class BaseDB(ABC):
    """
    Abstract base class for all database backends used to store
    EDA-schema data tables and graph-structured data.

    This class defines the interface that concrete database implementations
    (e.g., SQLiteDB, DuckDB, PostgreSQLDB, InMemoryDB) must follow.
    """

    # ------------------------------------------------------------------
    # Dataset / Table Management
    # ------------------------------------------------------------------
    @abstractmethod
    def create_dataset_tables(self) -> None:
        """
        Create all required tables for every entity defined in SchemaMetadata.

        Implementations may:
            - Create SQL tables
            - Create Parquet files
            - Initialize in-memory structures
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Graph Storage
    # ------------------------------------------------------------------
    @abstractmethod
    def add_graph_data(self, entity_name: str, graph: Any, key: str) -> None:
        """
        Store graph data for a graph-based entity.

        Args:
            entity_name (str): Name of the entity (e.g. "netlists").
            graph (Any): Graph object (typically a NetworkX DiGraph).
            key (str): Unique identifier for the graph record.
        """
        raise NotImplementedError

    @abstractmethod
    def get_graph_data(self, entity_name: str, key: str) -> Dict[str, Any]:
        """
        Retrieve a stored graph for a given entity and key.

        Args:
            entity_name (str): Name of the graph entity.
            key (str): Unique identifier for the graph.

        Returns:
            dict: Graph data in dictionary form, suitable for reconstruction.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Tabular Data
    # ------------------------------------------------------------------
    @abstractmethod
    def add_table_row(self, entity_name: str, row: Dict[str, Any]) -> None:
        """
        Insert a single row into a table.

        Args:
            entity_name (str): Name of the entity table (e.g. "gates").
            row (dict): A dictionary representing one row of data.
        """
        raise NotImplementedError

    @abstractmethod
    def add_table_data(self, entity_name: str, data: List[Dict[str, Any]]) -> None:
        """
        Insert multiple rows into a table.

        Args:
            entity_name (str): Name of the entity table.
            data (list[dict]): Multiple rows of data as a list of dictionaries.
        """
        raise NotImplementedError

    @abstractmethod
    def get_table_data(self, entity_name: str, **filters: Any) -> pd.DataFrame:
        """
        Retrieve filtered data from a table.

        Args:
            entity_name (str): Name of the table.
            **filters: Arbitrary column=value filters.

        Returns:
            pd.DataFrame: Rows matching the filtering criteria.
        """
        raise NotImplementedError

    @abstractmethod
    def get_table_row(self, entity_name: str, **filters: Any) -> pd.Series:
        """
        Retrieve a single row from a table.

        Args:
            entity_name (str): Name of the table.
            **filters: Filtering criteria (must uniquely identify one row).

        Returns:
            pd.Series: A single row corresponding to the filter.
        """
        raise NotImplementedError

    def get_entity(self, entity_name: str, **key_fields):
        """
        Retrieve a fully constructed entity instance, including its graph if applicable.
        Requires all primary-key fields to be supplied via key_fields.

        Args:
            entity_name (str): Entity type.
            **key_fields: Mapping of primary-key columns → values.

        Returns:
            BaseEntity: Fully reconstructed entity.

        Raises:
            ValueError: If PKs are missing.
            DataNotFoundError: If no matching row exists.
        """
        # --------------------------------------------------------------
        # Validate entity type
        # --------------------------------------------------------------
        if entity_name not in entity.SchemaMetadata._ENTITY_MODELS:
            raise ValueError(f"Unknown entity '{entity_name}'")

        model_cls = entity.SchemaMetadata._ENTITY_MODELS[entity_name]

        # --------------------------------------------------------------
        # Validate primary keys
        # --------------------------------------------------------------
        pk_cols = entity.SchemaMetadata.get_pk_columns(entity_name)
        if not pk_cols:
            raise ValueError(f"Entity '{entity_name}' has no defined primary-key fields")

        missing = [pk for pk in pk_cols if pk not in key_fields]
        if missing:
            raise ValueError(
                f"Missing primary-key values for '{entity_name}': {missing}. "
                f"Required: {pk_cols}"
            )

        # --------------------------------------------------------------
        # Load row from table using PKs
        # --------------------------------------------------------------
        row = self.get_table_row(entity_name, **key_fields)
        obj = model_cls(**row.to_dict())

        # --------------------------------------------------------------
        # Attach graph (if graph entity)
        # --------------------------------------------------------------
        if entity.SchemaMetadata.is_graph_entity(entity_name):
            gdict = self.get_graph_data(entity_name, **key_fields)
            obj.load_graph_dict(gdict)

        return obj
