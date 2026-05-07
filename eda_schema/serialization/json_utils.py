"""
JSON serialization utilities for EDA Schema entities.

This module provides functions to load and save EDA-schema entities to/from JSON files.
"""

import json
from dataclasses import asdict
from typing import Type

from eda_schema.base import BaseEntity
from eda_schema.errors import EDASchemaError


def load_json(home: str, schema_class: Type[BaseEntity]) -> BaseEntity:
    """
    Load JSON data from a file, validate it using the given schema, and create a schema object.

    Args:
        home (str): Directory where JSON file is located.
        schema_class (class): The schema class to use for validation and object creation.

    Returns:
        BaseEntity: Instance of the schema object loaded with validated JSON data.
    """
    if not issubclass(schema_class, BaseEntity):
        raise EDASchemaError("schema_class must be a subclass of BaseEntity")

    # Use entity name or title as fallback
    entity_name = schema_class.__name__.lower()
    json_path = f"{home}/{entity_name}.json"

    with open(json_path, "r", encoding="utf-8") as openfile:
        json_data = json.load(openfile)

    # Filter out internal fields (those starting with _)
    filtered_data = {k: v for k, v in json_data.items() if not k.startswith('_')}

    # Use the load classmethod to create instance from data
    schema_object = schema_class.load(filtered_data)
    return schema_object


def dump_json(home: str, schema_object: BaseEntity, suffix: str) -> None:
    """
    Dump schema object data into a JSON file.

    Args:
        home (str): Directory where JSON file will be saved.
        schema_object (BaseEntity): The schema object to be serialized into JSON.
        suffix (str): Suffix to append to the filename.
    """
    if not isinstance(schema_object, BaseEntity):
        raise EDASchemaError("schema_object must be an instance of BaseEntity")

    data_dict = asdict(schema_object)
    # Use entity name or title as fallback
    entity_name = getattr(schema_object, 'title', None) or type(schema_object).__name__.lower()
    json_path = f"{home}/{entity_name}/{suffix}.json"

    with open(json_path, "w", encoding="utf-8") as outfile:
        json.dump(data_dict, outfile)
