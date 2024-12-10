from typing import Dict, Any

import jsonschema
import networkx as nx

from eda_schema.errors import ValidationError


class BaseEntity:
    """Base class for JSON schema validation and attribute setting."""

    def __init__(self, json_data: Dict[str, Any] = None, validate: bool = True) -> None:
        """
        Initialize the BaseEntity instance.

        Args:
            json_data (dict, optional): JSON data to validate and set as attributes.
            validate (bool, optional): Whether to validate the JSON data before setting attributes. Defaults to True.
        """
        if json_data:
            self.load(json_data, validate=validate)

    def load(self, json_data: Dict[str, Any], validate: bool = True) -> None:
        """
        Load and validate JSON data, setting attributes.

        Args:
            json_data (dict): JSON data to load and validate.
            validate (bool, optional): Whether to validate the JSON data before setting attributes. Defaults to True.
        """
        if validate:
            self.validate(json_data)
        for attr, value in json_data.items():
            setattr(self, attr, value)

    def validate(self, json_data: Dict[str, Any]) -> None:
        """
        Validate JSON data against the schema.

        Args:
            json_data (dict): JSON data to validate.

        Raises:
            ValidationError: If JSON data does not conform to the schema.
        """
        try:
            jsonschema.validate([json_data], self.schema)
        except jsonschema.exceptions.ValidationError as msg:
            raise ValidationError(msg)

    def asdict(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary representation.

        Returns:
            dict: Dictionary representation of the object attributes.
        """
        return {attr: getattr(self, attr) for attr in self.schema["items"]["properties"]}

    def __repr__(self):
        return str(self.asdict())

    def __str__(self):
        return str(self.asdict())


class GraphEntity(nx.DiGraph, BaseEntity):
    """Base class for JSON schema validation and attribute setting."""

    def __init__(self, json_data: Dict[str, Any] = None) -> None:
        """
        Initialize the BaseEntity instance.

        Args:
            json_data (dict, optional): JSON data to validate and set as attributes.
        """
        super().__init__()
        if json_data:
            self.load(json_data)

    def __repr__(self):
        return str(self.asdict())

    def __str__(self):
        return str(self.asdict())

    def graph_dict(self):
        return {
            "nodes": [node for node in self.nodes],
            "node_types": [self.nodes[node]["type"] for node in self.nodes],
            "edges": [list(edge) for edge in self.edges],
        }
