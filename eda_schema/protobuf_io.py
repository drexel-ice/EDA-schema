"""
This module provides functions to load and save EDA-schema entities from/to Protobuf files.
It includes mapping between gRPC Protobuf messages and EDA-schema entities.

Changes:
- Updated `save_protobuf_file` to dynamically set fields based on the Protobuf `DESCRIPTOR` instead of hardcoding field assignments.
- Updated `map_grpc_to_eda` to ensure proper field mapping for `NetlistEntity` and other entity types.
"""

import eda_schema.eda_schema_pb2 as pb2
from eda_schema.entity import NetlistEntity, PowerMetricsEntity, StandardCellEntity
from eda_schema.errors import ValidationError

def load_protobuf_file(file_path):
    """Reads a Protobuf file and converts it to an EDA-schema entity."""
    entity_message = pb2.EntityMessage()
    with open(file_path, "rb") as f:
        entity_message.ParseFromString(f.read())
    return map_grpc_to_eda(entity_message)


# TODO: Remove this function - Keeping this in for code review.
def x_save_protobuf_file(entity, file_path):
    """Converts an EDA-schema entity to Protobuf and writes it to a file."""
    entity_message = pb2.EntityMessage()
    entity_message.name = entity.name
    entity_message.id = entity.id
    entity_message.type = entity.type
    with open(file_path, "wb") as f:
        f.write(entity_message.SerializeToString())
        

def save_protobuf_file(entity, file_path, entity_class="EntityMessage"):
    """
    Converts an EDA-schema entity to Protobuf and writes it to a file.

    Args:
        entity: An instance of the entity (with attributes matching proto fields).
        file_path: Path to save serialized protobuf.
        entity_class: String name of the pb2 message class (default = "EntityMessage").
    """
    entity_cls = getattr(pb2, entity_class)
    entity_message = entity_cls()

    # Dynamically set fields based on DESCRIPTOR
    for field in entity_message.DESCRIPTOR.fields:
        value = getattr(entity, field.name)
        
        if field.label == field.LABEL_REPEATED:  # Repeated field (list of messages or scalars)
            repeated_container = getattr(entity_message, field.name)
            repeated_container.extend(value)
        
        elif field.message_type:  # Single nested message type
            getattr(entity_message, field.name).CopyFrom(value)
        
        else:  # Scalar field (int, string, etc.)
            setattr(entity_message, field.name, value)

    # Write serialized protobuf to file
    with open(file_path, "wb") as f:
        f.write(entity_message.SerializeToString())

def fetch_from_eda_schema(entity_id):
    """Dummy implementation for testing."""
    entity = pb2.EntityMessage()
    entity.name = "DummyEntity"
    entity.id = int(entity_id)
    entity.type = "Netlist"
    return entity
# You can return a mock object or raise NotImplementedError
# raise NotImplementedError("fetch_from_eda_schema is not implemented yet.")

def map_grpc_to_eda(grpc_message):
    """Converts a gRPC Protobuf message to an EDA-schema entity with proper field mapping."""
    if grpc_message.type == "Netlist":
        return NetlistEntity({
            "width": grpc_message.width,  # TODO: CHANGE - Ensure these fields exist in .proto
            "height": grpc_message.height,
            "no_of_inputs": grpc_message.no_of_inputs,
            "no_of_outputs": grpc_message.no_of_outputs,
            "no_of_cells": grpc_message.no_of_cells,
            "no_of_nets": grpc_message.no_of_nets,
            "cell_density": grpc_message.cell_density,
            "pin_density": grpc_message.pin_density,
            "net_density": grpc_message.net_density,
            "utilization": grpc_message.utilization,
        })
    elif grpc_message.type == "PowerMetrics":
        return PowerMetricsEntity({
            "internal_power": grpc_message.internal_power,
            "switching_power": grpc_message.switching_power,
            "leakage_power": grpc_message.leakage_power,
            "combinational_power": grpc_message.combinational_power,
            "sequential_power": grpc_message.sequential_power,
            "macro_power": grpc_message.macro_power,
            "total_power": grpc_message.total_power,
        })
    elif grpc_message.type == "StandardCell":
        return StandardCellEntity({
            "name": grpc_message.name,
            "width": grpc_message.width,
            "height": grpc_message.height,
            "no_of_input_pins": grpc_message.no_of_input_pins,
            "no_of_output_pins": grpc_message.no_of_output_pins,
            "is_sequential": grpc_message.is_sequential,
            "is_inverter": grpc_message.is_inverter,
            "is_buffer": grpc_message.is_buffer,
            "drive_strength": grpc_message.drive_strength,
        })
    else:
        raise ValidationError(f"Unknown entity type: {grpc_message.type}")
