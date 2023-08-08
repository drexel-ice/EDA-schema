import json
from typing import Type
from eda_schema.base import BaseSchema
from eda_schema.errors import EDASchemaError

def load_json(home: str, schema_class: Type[BaseSchema]) -> BaseSchema:
    """
    Load JSON data from a file, validate it using the given schema, and create a schema object.

    Args:
        home (str): Directory where JSON file is located.
        schema_class (class): The schema class to use for validation and object creation.

    Returns:
        BaseSchema: Instance of the schema object loaded with validated JSON data.
    """
    if not issubclass(schema_class, BaseSchema):
        raise EDASchemaError("schema_class must be a subclass of BaseSchema")

    schema_object = schema_class()
    with open(f"{home}/{schema_object.title}.json", "r") as openfile:
        json_data = json.load(openfile)

    schema_object.load(json_data)
    return schema_object


def dump_json(home: str, schema_object: BaseSchema) -> None:
    """
    Dump schema object data into a JSON file.

    Args:
        home (str): Directory where JSON file will be saved.
        schema_object (BaseSchema): The schema object to be serialized into JSON.
    """
    if not isinstance(schema_object, BaseSchema):
        raise EDASchemaError("schema_object must be an instance of BaseSchema")

    data_dict = schema_object.asdict()
    with open(f"{home}/{schema_object.title}.json", "w") as outfile:
        json.dump(data_dict, outfile)
