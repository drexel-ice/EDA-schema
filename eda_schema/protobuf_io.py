import eda_schema.eda_schema_pb2 as pb2
from eda_schema.entity import NetlistEntity, PowerMetricsEntity, StandardCellEntity
from eda_schema.errors import ValidationError

def load_protobuf_file(file_path):
    """Reads a Protobuf file and converts it to an EDA-schema entity."""
    entity_message = pb2.EntityMessage()

    with open(file_path, "rb") as f:
        entity_message.ParseFromString(f.read())

    return map_grpc_to_eda(entity_message)


def save_protobuf_file(entity, file_path):
    """Converts an EDA-schema entity to Protobuf and writes it to a file."""
    entity_message = pb2.EntityMessage()
    entity_message.type = entity.__class__.__name__

    for field in entity.__dict__:
        setattr(entity_message, field, getattr(entity, field))

    with open(file_path, "wb") as f:
        f.write(entity_message.SerializeToString())


def map_grpc_to_eda(grpc_message):
    """Converts a gRPC Protobuf message to an EDA-schema entity with proper field mapping."""
    if grpc_message.type == "Netlist":
        return NetlistEntity({
            "width": grpc_message.width,
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