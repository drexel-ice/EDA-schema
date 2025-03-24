"""
This module provides functions to load and save EDA-schema entities from/to Protobuf files.
It includes mapping between gRPC Protobuf messages and EDA-schema entities.

Changes:
- Updated `save_protobuf_file` to dynamically set fields based on the Protobuf `DESCRIPTOR` instead of hardcoding field assignments.
- Updated `map_grpc_to_eda` to ensure proper field mapping for `NetlistEntity` and other entity types.
- Added `load_pb` function to directly load protobuf files into specific object types.
"""

import eda_schema.eda_schema_pb2 as pb2
from eda_schema.entity import NetlistEntity, PowerMetricsEntity, StandardCellEntity
from eda_schema.errors import ValidationError

def x_load_protobuf_file(file_path):
    """Reads a Protobuf file and converts it to an EDA-schema entity."""
    entity_message = pb2.EntityMessage()
    with open(file_path, "rb") as f:
        entity_message.ParseFromString(f.read())
    return map_grpc_to_eda(entity_message)

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

def dataset_to_protobuf(netlist):
    """
    Convert a netlist from the dataset into a protobuf object.
    
    Args:
        netlist: The netlist object to convert
        
    Returns:
        pb2.NetlistEntity: The populated protobuf object
    """
    # Create a new NetlistEntity protobuf message
    netlist_proto = pb2.NetlistEntity()
    
    # Populate basic netlist properties
    if hasattr(netlist, 'width'):
        netlist_proto.width = float(netlist.width)
    if hasattr(netlist, 'height'):
        netlist_proto.height = float(netlist.height)
    if hasattr(netlist, 'no_of_inputs'):
        netlist_proto.no_of_inputs = int(netlist.no_of_inputs)
    if hasattr(netlist, 'no_of_outputs'):
        netlist_proto.no_of_outputs = int(netlist.no_of_outputs)
    if hasattr(netlist, 'utilization'):
        netlist_proto.utilization = float(netlist.utilization)
    if hasattr(netlist, 'cell_density'):
        netlist_proto.cell_density = float(netlist.cell_density)
    if hasattr(netlist, 'pin_density'):
        netlist_proto.pin_density = float(netlist.pin_density)
    if hasattr(netlist, 'net_density'):
        netlist_proto.net_density = float(netlist.net_density)
        
    # Populate cell metrics - access attributes directly
    if hasattr(netlist, 'cell_metrics'):
        cm = netlist.cell_metrics
        if hasattr(cm, 'no_of_combinational_cells'):
            netlist_proto.cell_metrics.no_of_combinational_cells = int(cm.no_of_combinational_cells)
        if hasattr(cm, 'no_of_sequential_cells'):
            netlist_proto.cell_metrics.no_of_sequential_cells = int(cm.no_of_sequential_cells)
        if hasattr(cm, 'no_of_buffers'):
            netlist_proto.cell_metrics.no_of_buffers = int(cm.no_of_buffers)
        if hasattr(cm, 'no_of_inverters'):
            netlist_proto.cell_metrics.no_of_inverters = int(cm.no_of_inverters)
        if hasattr(cm, 'no_of_fillers'):
            netlist_proto.cell_metrics.no_of_fillers = int(cm.no_of_fillers)
        if hasattr(cm, 'no_of_tap_cells'):
            netlist_proto.cell_metrics.no_of_tap_cells = int(cm.no_of_tap_cells)
        if hasattr(cm, 'no_of_diodes'):
            netlist_proto.cell_metrics.no_of_diodes = int(cm.no_of_diodes)
        if hasattr(cm, 'no_of_macros'):
            netlist_proto.cell_metrics.no_of_macros = int(cm.no_of_macros)
        if hasattr(cm, 'no_of_total_cells'):
            netlist_proto.cell_metrics.no_of_total_cells = int(cm.no_of_total_cells)
            
    # Populate area metrics - access attributes directly
    if hasattr(netlist, 'area_metrics'):
        am = netlist.area_metrics
        if hasattr(am, 'combinational_cell_area'):
            netlist_proto.area_metrics.combinational_cell_area = float(am.combinational_cell_area)
        if hasattr(am, 'sequential_cell_area'):
            netlist_proto.area_metrics.sequential_cell_area = float(am.sequential_cell_area)
        if hasattr(am, 'buffer_area'):
            netlist_proto.area_metrics.buffer_area = float(am.buffer_area)
        if hasattr(am, 'inverter_area'):
            netlist_proto.area_metrics.inverter_area = float(am.inverter_area)
        if hasattr(am, 'filler_area'):
            netlist_proto.area_metrics.filler_area = float(am.filler_area)
        if hasattr(am, 'tap_cell_area'):
            netlist_proto.area_metrics.tap_cell_area = float(am.tap_cell_area)
        if hasattr(am, 'diode_area'):
            netlist_proto.area_metrics.diode_area = float(am.diode_area)
        if hasattr(am, 'macro_area'):
            netlist_proto.area_metrics.macro_area = float(am.macro_area)
        if hasattr(am, 'cell_area'):
            netlist_proto.area_metrics.cell_area = float(am.cell_area)
        if hasattr(am, 'total_area'):
            netlist_proto.area_metrics.total_area = float(am.total_area)
            
    # Populate power metrics - access attributes directly
    if hasattr(netlist, 'power_metrics'):
        pm = netlist.power_metrics
        if hasattr(pm, 'combinational_power'):
            netlist_proto.power_metrics.combinational_power = float(pm.combinational_power)
        if hasattr(pm, 'sequential_power'):
            netlist_proto.power_metrics.sequential_power = float(pm.sequential_power)
        if hasattr(pm, 'macro_power'):
            netlist_proto.power_metrics.macro_power = float(pm.macro_power)
        if hasattr(pm, 'internal_power'):
            netlist_proto.power_metrics.internal_power = float(pm.internal_power)
        if hasattr(pm, 'switching_power'):
            netlist_proto.power_metrics.switching_power = float(pm.switching_power)
        if hasattr(pm, 'leakage_power'):
            netlist_proto.power_metrics.leakage_power = float(pm.leakage_power)
        if hasattr(pm, 'total_power'):
            netlist_proto.power_metrics.total_power = float(pm.total_power)
            
    # Populate critical path metrics - access attributes directly
    if hasattr(netlist, 'critical_path_metrics'):
        cpm = netlist.critical_path_metrics
        if hasattr(cpm, 'startpoint'):
            netlist_proto.critical_path_metrics.startpoint = str(cpm.startpoint)
        if hasattr(cpm, 'endpoint'):
            netlist_proto.critical_path_metrics.endpoint = str(cpm.endpoint)
        if hasattr(cpm, 'worst_arrival_time'):
            netlist_proto.critical_path_metrics.worst_arrival_time = float(cpm.worst_arrival_time)
        if hasattr(cpm, 'worst_slack'):
            netlist_proto.critical_path_metrics.worst_slack = float(cpm.worst_slack)
        if hasattr(cpm, 'total_negative_slack'):
            netlist_proto.critical_path_metrics.total_negative_slack = float(cpm.total_negative_slack)
        if hasattr(cpm, 'no_of_timing_paths'):
            netlist_proto.critical_path_metrics.no_of_timing_paths = int(cpm.no_of_timing_paths)
        if hasattr(cpm, 'no_of_slack_violations'):
            netlist_proto.critical_path_metrics.no_of_slack_violations = int(cpm.no_of_slack_violations)
    
    # Populate timing paths
    if hasattr(netlist, 'timing_paths'):
        for path_type, paths in netlist.timing_paths.items():
            for path in paths:
                path_proto = netlist_proto.timing_paths.add()
                if 'startpoint' in path:
                    path_proto.startpoint = str(path['startpoint'])
                if 'endpoint' in path:
                    path_proto.endpoint = str(path['endpoint'])
                if 'path_type' in path:
                    path_proto.path_type = str(path['path_type'])
                if 'arrival_time' in path:
                    path_proto.arrival_time = float(path['arrival_time'])
                if 'required_time' in path:
                    path_proto.required_time = float(path['required_time'])
                if 'slack' in path:
                    path_proto.slack = float(path['slack'])
                if 'no_of_gates' in path:
                    path_proto.no_of_gates = int(path['no_of_gates'])
                if 'is_critical_path' in path and path['is_critical_path'] is not None:
                    path_proto.is_critical_path = bool(path['is_critical_path'])
    
    for node in list(netlist.nodes):
        if netlist.nodes[node]['type'] == "IO_PORT":
            io_port_entity = netlist.nodes[node]['entity']
            io_port_proto = netlist_proto.io_ports.add()

            io_port_proto.direction = io_port_entity.direction
            io_port_proto.x = io_port_entity.x
            io_port_proto.y = io_port_entity.y
            io_port_proto.capacitance = io_port_entity.capacitance or 0

    return netlist_proto

def load_protobuf_file(filename, type_name="NetlistEntity"):
    """
    Load and parse a protobuf file into the corresponding object type.
    
    This function deserializes a binary protobuf file into a Python object 
    that corresponds to the specified protobuf message type. It handles
    different types of protobuf messages defined in the schema, with NetlistEntity
    as the default type.
    
    The function dynamically imports the appropriate protobuf message class
    based on the provided type_name parameter, which allows loading different
    types of protobuf messages without modifying the code.
    
    Args:
        filename (str): Path to the protobuf file to be loaded
        type_name (str): Name of the protobuf message class to use for parsing
                        (default: "NetlistEntity")
        
    Returns:
        object: The parsed protobuf object if successful, None otherwise
        
    Example:
        # Load a netlist from a protobuf file
        netlist = load_pb("path/to/netlist.pb")
        
        # Load cell metrics from a protobuf file
        cell_metrics = load_pb("path/to/metrics.pb", "CellMetricsEntity")
    """
    try:
        # Dynamically get the appropriate message class from pb2 module
        # This allows us to handle different protobuf message types without
        # having to write separate loading functions for each type
        message_class = getattr(pb2, type_name)
        
        # Create an empty instance of the message class
        # This will be populated with the data from the protobuf file
        message = message_class()
        
        # Open the file in binary mode (protobuf is a binary format)
        # and read its contents into the message object
        with open(filename, "rb") as f:
            # ParseFromString deserializes the binary data into the message object
            # converting it from the wire format into a Python object
            message.ParseFromString(f.read())
            
        # Log success message with type and filename for debugging
        print(f"Successfully loaded {type_name} from {filename}")
        
        # Return the populated message object to the caller
        return message
        
    except AttributeError:
        # This exception occurs if type_name is not a valid protobuf message class
        print(f"Error: {type_name} is not a valid protobuf message type")
        import traceback
        traceback.print_exc()
        return None
    except FileNotFoundError:
        # This exception occurs if the specified file doesn't exist
        print(f"Error: The file {filename} was not found")
        return None
    except Exception as e:
        # Catch any other exceptions that might occur during loading
        # This could include invalid protobuf format, permission errors, etc.
        print(f"Error loading protobuf file: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
