# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/db/base.py
# Authors :
#     Pratik Shrestha       <ps937@drexel.edu>
#
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike
# 4.0 International License (CC BY-NC-SA 4.0). You may obtain a copy of the
# license at: https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. Commercial use is
# expressly prohibited; derivative works must be shared under the same
# license terms (ShareAlike).

import warnings
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

from eda_schema import entity
from eda_schema.base import Image2D
from eda_schema.errors import DataNotFoundError


class BaseDB(metaclass=ABCMeta):
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
    def add_graph_data(self, entity_name: str, graph: Any, **key_fields) -> None:
        """
        Store graph data for a graph-based entity.

        Args:
            entity_name (str): Name of the entity (e.g. "netlists").
            graph (Any): Graph object (typically a NetworkX DiGraph or dict).
            **key_fields: Primary-key values identifying the graph record
                        (e.g. flow_id="X", stage="Y").
        """
        raise NotImplementedError

    @abstractmethod
    def get_graph_data(self, entity_name: str, **key_fields) -> Dict[str, Any]:
        """
        Retrieve a stored graph for a given entity and key fields.

        Args:
            entity_name (str): Name of the graph entity.
            **key_fields: Primary-key values identifying the graph
                        (e.g. flow_id="X", stage="Y").

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
    def add_image(
        self, entity_name: str, image_name: str, image: Image2D, **key_fields
    ) -> None:
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

        # Handle Dict[str, Image2D] fields
        dict_images = entity_obj.get_dict_image_data()
        for dict_field_name, dict_value in dict_images.items():
            if not dict_value:
                continue
            for key, image_obj in dict_value.items():
                if image_obj is None:
                    continue
                # Store with naming scheme: field_name__dict_key
                image_name = f"{dict_field_name}__{key}"
                self.add_image(
                    entity_name,
                    image_name=image_name,
                    image=image_obj,
                    **key_fields,
                )

    # ------------------------------------------------------------------
    # Helper methods for graph key resolution
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_graph_key(key: Optional[str], key_fields: Dict[str, Any]) -> str:
        """
        Resolve graph key from either legacy 'key' parameter or new 'key_fields'.

        This helper method standardizes key construction across all database backends
        that support backward compatibility with the legacy 'key: str' API.

        Args:
            key: Legacy key string (optional, deprecated).
            key_fields: Primary key fields dictionary (preferred).

        Returns:
            str: Resolved key string constructed from key_fields or returned from key.

        Raises:
            ValueError: If neither key nor key_fields are provided, or if key is empty.
        """
        if key is None:
            if not key_fields:
                raise ValueError(
                    "Either 'key' (legacy) or 'key_fields' (primary keys) must be provided. "
                    "Use **key_fields for consistency with other backends."
                )
            # Construct key from sorted key_fields for consistency
            return "__".join(f"{k}={v}" for k, v in sorted(key_fields.items()))
        if key_fields:
            # If both provided, key_fields takes precedence
            warnings.warn(
                "Both 'key' and 'key_fields' provided. Using 'key_fields'. "
                "The 'key' parameter is deprecated.",
                DeprecationWarning,
                stacklevel=3,
            )
            return "__".join(f"{k}={v}" for k, v in sorted(key_fields.items()))
        if not key:
            raise ValueError(
                "Either 'key' (legacy) or 'key_fields' (primary keys) must be provided. "
                "Use **key_fields for consistency with other backends."
            )
        return key

    # ------------------------------------------------------------------
    # Combined entity
    # ------------------------------------------------------------------
    def get_entity(
        self, entity_name: str, load_sub_entities: bool = True, **key_fields
    ) -> Any:
        """
        Retrieve a fully constructed entity instance, including its graph if applicable.
        Requires all primary-key fields to be supplied via key_fields.

        Args:
            entity_name (str): Entity type.
            load_sub_entities (bool): Whether to load the sub-entities if applicable.
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
            raise ValueError(
                f"Entity '{entity_name}' has no defined primary-key fields"
            )

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
        # Filter out internal metadata columns (start with _)
        row_dict = {k: v for k, v in row.to_dict().items() if not k.startswith("_")}
        obj = model_cls(**row_dict)

        # --------------------------------------------------------------
        # Attach graph (if graph entity)
        # --------------------------------------------------------------
        if entity.SchemaMetadata.is_graph_entity(entity_name):
            graph_data = self.get_graph_data(entity_name, **key_fields)
            obj.load_graph_data(graph_data)
            if load_sub_entities:
                for node_type, node_cls in obj.NODE_TYPES.items():
                    node_entity_name = node_type.lower() + "s"
                    node_fields = {
                        k: v
                        for k, v in key_fields.items()
                        if k in entity.SchemaMetadata.get_columns(node_entity_name)
                    }
                    if (
                        entity_name == "timing_paths"
                        and node_type in ["PIN", "PORT"]
                        or entity_name == "clock_trees"
                    ):
                        pins = [
                            tp_node
                            for tp_node, tp_node_type in zip(
                                graph_data["nodes"], graph_data["node_types"]
                            )
                            if tp_node_type == node_type
                        ]
                        node_fields["name"] = pins

                    node_data_id = "name"
                    if node_type == "NET_ARC":
                        node_data_id = "net_name"
                    if node_type == "CELL_ARC":
                        node_data_id = "gate_name"

                    node_data = self.get_table_data(node_entity_name, **node_fields)
                    for row in node_data.itertuples(index=False):
                        row_dict = row._asdict()
                        obj.nodes[row_dict[node_data_id]]["entity"] = node_cls(
                            **row_dict
                        )

        # --------------------------------------------------------------
        # Load Image2D fields for this entity (if any exist)
        # --------------------------------------------------------------
        if load_sub_entities:
            for image_field in obj._image_keys:
                try:
                    image = self.get_image(entity_name, image_field, **key_fields)
                    setattr(obj, image_field, image)
                except DataNotFoundError:
                    setattr(obj, image_field, None)

        # --------------------------------------------------------------
        # Load Dict[str, Image2D] fields for this entity (if any exist)
        # --------------------------------------------------------------
        for dict_image_field in obj._dict_image_keys:
            dict_value = {}
            # Try to discover images by attempting to load with common patterns
            # For now, we'll try a few common metal layer names
            # A more robust solution would store a manifest, but this works for routing_by_metal
            common_keys = [
                "met1",
                "met2",
                "met3",
                "met4",
                "met5",
                "metal1",
                "metal2",
                "metal3",
                "metal4",
                "metal5",
            ]
            for dict_key in common_keys:
                try:
                    image = self.get_image(
                        entity_name, f"{dict_image_field}__{dict_key}", **key_fields
                    )
                    dict_value[dict_key] = image
                except DataNotFoundError:
                    pass
            # Also try to discover by listing files if the backend supports it
            # This is backend-specific, so we'll handle it in subclasses if needed
            setattr(obj, dict_image_field, dict_value)

        return obj
