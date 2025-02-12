import json
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

    schema_object = schema_class()
    with open(f"{home}/{schema_object.title}.json", "r") as openfile:
        json_data = json.load(openfile)

    schema_object.load(json_data)
    return schema_object


def dump_json(home: str, schema_object: BaseEntity, suffix: str) -> None:
    """
    Dump schema object data into a JSON file.

    Args:
        home (str): Directory where JSON file will be saved.
        schema_object (BaseEntity): The schema object to be serialized into JSON.
    """
    if not isinstance(schema_object, BaseEntity):
        raise EDASchemaError("schema_object must be an instance of BaseEntity")

    data_dict = schema_object.asdict()
    with open(f"{home}/{schema_object.title}/{suffix}.json", "w") as outfile:
        json.dump(data_dict, outfile)
