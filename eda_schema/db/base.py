from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd

from eda_schema import entity
from eda_schema.base import Image2D
from eda_schema.errors import DataNotFoundError


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

    # ------------------------------------------------------------------
    # Image Storage
    # ------------------------------------------------------------------
    @abstractmethod
    def add_image(self, entity_name: str, image_name: str, image: Image2D, **key_fields) -> None:
        """
        Store an Image2D associated with an entity row.

        Args:
            entity_name (str): Name of the entity (e.g. "netlists").
            image_name (str): Name of the image field (e.g. "cell_placement").
            image (Image2D): The image to store.
            **key_fields: Primary key values identifying the row
                        (e.g. flow_id="X", stage="Y").
        """
        raise NotImplementedError

    @abstractmethod
    def get_image(self, entity_name: str, field: str, **key_fields) -> Image2D:
        """
        Retrieve an Image2D stored for a specific entity row.

        Args:
            entity_name (str): Name of the entity (e.g. "netlists").
            field (str): Name of the stored image field.
            **key_fields: Primary key values identifying the row.

        Returns:
            Image2D: The loaded image.
        """
        raise NotImplementedError

    def add_entity_images(self, entity_name: str, entity_obj: Any) -> None:
        """
        Store all Image2D fields from an entity instance.

        Args:
            entity_name (str): Name of the entity (e.g. "netlists").
            entity_obj: A BaseEntity subclass instance.
        """
        images = entity_obj.get_image_data()

        # Extract primary keys from the entity instance
        key_fields = {pk: getattr(entity_obj, pk) for pk in entity_obj._primary_keys}

        for image_name, image_obj in images.items():
            if image_obj is None:
                continue
            self.add_image(
                entity_name,
                image_name=image_name,
                image=image_obj,
                **key_fields,
            )

    # ------------------------------------------------------------------
    # Combined entity
    # ------------------------------------------------------------------
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
        model_cls = entity.SchemaMetadata.get_model(entity_name)
        if model_cls is None:
            raise ValueError(f"Unknown entity '{entity_name}'")

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
            graph_data = self.get_graph_data(entity_name, **key_fields)
            obj.load_graph_data(graph_data)
            for node_type, node_cls in obj.NODE_TYPES.items():
                node_entity_name = node_type.lower() + "s"
                node_fields = {k: v for k, v in key_fields.items() if k in entity.SchemaMetadata.get_columns(node_entity_name)}
                if entity_name == "timing_paths" and node_type in ["PIN", "PORT"] or entity_name == "clock_trees":
                    pins = [tp_node for tp_node, tp_node_type in zip(graph_data["nodes"], graph_data["node_types"]) if tp_node_type == node_type]
                    node_fields["name"] = pins

                node_data_id = "name"
                if node_type == "NET_ARC":
                    node_data_id = "net_name"
                if node_type == "CELL_ARC":
                    node_data_id = "gate_name"

                node_data = self.get_table_data(node_entity_name, **node_fields)
                for row in node_data.itertuples(index=False):
                    row_dict = row._asdict()
                    obj.nodes[row_dict[node_data_id]]["entity"] = node_cls(**row_dict)

        # --------------------------------------------------------------
        # Load Image2D fields for this entity (if any exist)
        # --------------------------------------------------------------
        for image_field in obj._image_keys:
            try:
                image = self.get_image(entity_name, image_field, **key_fields)
                setattr(obj, image_field, image)
            except DataNotFoundError:
                setattr(obj, image_field, None)

        return obj
