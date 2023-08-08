import jsonschema
from typing import Dict, Any

from eda_schema.errors import ValidationError


class BaseSchema:
    """Base class for JSON schema validation and attribute setting."""

    def __init__(self, json_data: Dict[str, Any] = None) -> None:
        """
        Initialize the BaseSchema instance.

        Args:
            json_data (dict, optional): JSON data to validate and set as attributes.
        """
        if json_data:
            self.load(json_data)
    
    def load(self, json_data: Dict[str, Any]) -> None:
        """
        Load and validate JSON data, setting attributes.

        Args:
            json_data (dict): JSON data to load and validate.
        """
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
