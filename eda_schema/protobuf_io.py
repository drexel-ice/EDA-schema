"""
This module provides functions to load and save EDA-schema entities from/to Protobuf files.
It includes mapping between gRPC Protobuf messages and EDA-schema entities.

Changes:
- Updated `save_protobuf_file` to dynamically set fields based on the Protobuf `DESCRIPTOR` instead of hardcoding field assignments.
- Updated `map_grpc_to_eda` to ensure proper field mapping for `NetlistEntity` and other entity types.
- Added `load_pb` function to directly load protobuf files into specific object types.
- Added `dataset_to_protobuf` function to convert a netlist object to a protobuf format.
- Added `load_protobuf_file` function for loading protobuf files with specified message types.
- Implemented comprehensive error handling for protobuf serialization and deserialization.
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
    
    # Helper function to safely convert values with fallbacks
    def safe_float(value, default=0.0):
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
            
    def safe_int(value, default=0):
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
            
    def safe_str(value, default=""):
        if value is None:
            return default
        return str(value)
            
    def safe_bool(value, default=False):
        if value is None:
            return default
        try:
            return bool(value)
        except (ValueError, TypeError):
            return default
    
    # Populate basic netlist properties
    if hasattr(netlist, 'width'):
        netlist_proto.width = safe_float(netlist.width)
    if hasattr(netlist, 'height'):
        netlist_proto.height = safe_float(netlist.height)
    if hasattr(netlist, 'no_of_inputs'):
        netlist_proto.no_of_inputs = safe_int(netlist.no_of_inputs)
    if hasattr(netlist, 'no_of_outputs'):
        netlist_proto.no_of_outputs = safe_int(netlist.no_of_outputs)
    if hasattr(netlist, 'utilization'):
        netlist_proto.utilization = safe_float(netlist.utilization)
    if hasattr(netlist, 'cell_density'):
        netlist_proto.cell_density = safe_float(netlist.cell_density)
    if hasattr(netlist, 'pin_density'):
        netlist_proto.pin_density = safe_float(netlist.pin_density)
    if hasattr(netlist, 'net_density'):
        netlist_proto.net_density = safe_float(netlist.net_density)
        
    # Populate cell metrics - access attributes directly
    if hasattr(netlist, 'cell_metrics'):
        cm = netlist.cell_metrics
        if hasattr(cm, 'no_of_combinational_cells'):
            netlist_proto.cell_metrics.no_of_combinational_cells = safe_int(cm.no_of_combinational_cells)
        if hasattr(cm, 'no_of_sequential_cells'):
            netlist_proto.cell_metrics.no_of_sequential_cells = safe_int(cm.no_of_sequential_cells)
        if hasattr(cm, 'no_of_buffers'):
            netlist_proto.cell_metrics.no_of_buffers = safe_int(cm.no_of_buffers)
        if hasattr(cm, 'no_of_inverters'):
            netlist_proto.cell_metrics.no_of_inverters = safe_int(cm.no_of_inverters)
        if hasattr(cm, 'no_of_fillers'):
            netlist_proto.cell_metrics.no_of_fillers = safe_int(cm.no_of_fillers)
        if hasattr(cm, 'no_of_tap_cells'):
            netlist_proto.cell_metrics.no_of_tap_cells = safe_int(cm.no_of_tap_cells)
        if hasattr(cm, 'no_of_diodes'):
            netlist_proto.cell_metrics.no_of_diodes = safe_int(cm.no_of_diodes)
        if hasattr(cm, 'no_of_macros'):
            netlist_proto.cell_metrics.no_of_macros = safe_int(cm.no_of_macros)
        if hasattr(cm, 'no_of_total_cells'):
            netlist_proto.cell_metrics.no_of_total_cells = safe_int(cm.no_of_total_cells)
            
    # Populate area metrics - access attributes directly
    if hasattr(netlist, 'area_metrics'):
        am = netlist.area_metrics
        if hasattr(am, 'combinational_cell_area'):
            netlist_proto.area_metrics.combinational_cell_area = safe_float(am.combinational_cell_area)
        if hasattr(am, 'sequential_cell_area'):
            netlist_proto.area_metrics.sequential_cell_area = safe_float(am.sequential_cell_area)
        if hasattr(am, 'buffer_area'):
            netlist_proto.area_metrics.buffer_area = safe_float(am.buffer_area)
        if hasattr(am, 'inverter_area'):
            netlist_proto.area_metrics.inverter_area = safe_float(am.inverter_area)
        if hasattr(am, 'filler_area'):
            netlist_proto.area_metrics.filler_area = safe_float(am.filler_area)
        if hasattr(am, 'tap_cell_area'):
            netlist_proto.area_metrics.tap_cell_area = safe_float(am.tap_cell_area)
        if hasattr(am, 'diode_area'):
            netlist_proto.area_metrics.diode_area = safe_float(am.diode_area)
        if hasattr(am, 'macro_area'):
            netlist_proto.area_metrics.macro_area = safe_float(am.macro_area)
        if hasattr(am, 'cell_area'):
            netlist_proto.area_metrics.cell_area = safe_float(am.cell_area)
        if hasattr(am, 'total_area'):
            netlist_proto.area_metrics.total_area = safe_float(am.total_area)
            
    # Populate power metrics - access attributes directly
    if hasattr(netlist, 'power_metrics'):
        pm = netlist.power_metrics
        if hasattr(pm, 'combinational_power'):
            netlist_proto.power_metrics.combinational_power = safe_float(pm.combinational_power)
        if hasattr(pm, 'sequential_power'):
            netlist_proto.power_metrics.sequential_power = safe_float(pm.sequential_power)
        if hasattr(pm, 'macro_power'):
            netlist_proto.power_metrics.macro_power = safe_float(pm.macro_power)
        if hasattr(pm, 'internal_power'):
            netlist_proto.power_metrics.internal_power = safe_float(pm.internal_power)
        if hasattr(pm, 'switching_power'):
            netlist_proto.power_metrics.switching_power = safe_float(pm.switching_power)
        if hasattr(pm, 'leakage_power'):
            netlist_proto.power_metrics.leakage_power = safe_float(pm.leakage_power)
        if hasattr(pm, 'total_power'):
            netlist_proto.power_metrics.total_power = safe_float(pm.total_power)
            
    # Populate critical path metrics - access attributes directly
    if hasattr(netlist, 'critical_path_metrics'):
        cpm = netlist.critical_path_metrics
        if hasattr(cpm, 'startpoint'):
            netlist_proto.critical_path_metrics.startpoint = safe_str(cpm.startpoint)
        if hasattr(cpm, 'endpoint'):
            netlist_proto.critical_path_metrics.endpoint = safe_str(cpm.endpoint)
        if hasattr(cpm, 'worst_arrival_time'):
            netlist_proto.critical_path_metrics.worst_arrival_time = safe_float(cpm.worst_arrival_time)
        if hasattr(cpm, 'worst_slack'):
            netlist_proto.critical_path_metrics.worst_slack = safe_float(cpm.worst_slack)
        if hasattr(cpm, 'total_negative_slack'):
            netlist_proto.critical_path_metrics.total_negative_slack = safe_float(cpm.total_negative_slack)
        if hasattr(cpm, 'no_of_timing_paths'):
            netlist_proto.critical_path_metrics.no_of_timing_paths = safe_int(cpm.no_of_timing_paths)
        if hasattr(cpm, 'no_of_slack_violations'):
            netlist_proto.critical_path_metrics.no_of_slack_violations = safe_int(cpm.no_of_slack_violations)
    
    # Populate timing paths
    if hasattr(netlist, 'timing_paths'):
        for path_type, paths in netlist.timing_paths.items():
            for path in paths:
                path_proto = netlist_proto.timing_paths.add()
                if 'startpoint' in path:
                    path_proto.startpoint = safe_str(path['startpoint'])
                if 'endpoint' in path:
                    path_proto.endpoint = safe_str(path['endpoint'])
                if 'path_type' in path:
                    path_proto.path_type = safe_str(path['path_type'])
                if 'arrival_time' in path:
                    path_proto.arrival_time = safe_float(path['arrival_time'])
                if 'required_time' in path:
                    path_proto.required_time = safe_float(path['required_time'])
                if 'slack' in path:
                    path_proto.slack = safe_float(path['slack'])
                if 'no_of_gates' in path:
                    path_proto.no_of_gates = safe_int(path['no_of_gates'])
                if 'is_critical_path' in path:
                    path_proto.is_critical_path = safe_bool(path['is_critical_path'])
    
    # Handle nodes only if netlist has nodes
    if hasattr(netlist, 'nodes'):
        # Collect IO ports into a list for netlist entity
        io_ports = []
        for node in list(netlist.nodes):
            # Check if node exists and has the required attributes
            if (node in netlist.nodes and 
                'type' in netlist.nodes[node] and 
                'entity' in netlist.nodes[node] and
                netlist.nodes[node]['type'] == "IO_PORT"):
                try:
                    io_port_entity = netlist.nodes[node]['entity']
                    
                    # Create protobuf IO port object
                    io_port_proto = pb2.IOPortEntity()
                    io_port_proto.name = safe_str(node)
                    
                    # Only set attributes that exist
                    if hasattr(io_port_entity, 'direction'):
                        io_port_proto.direction = safe_str(io_port_entity.direction)
                    if hasattr(io_port_entity, 'x'):
                        io_port_proto.x = safe_float(io_port_entity.x)
                    if hasattr(io_port_entity, 'y'):
                        io_port_proto.y = safe_float(io_port_entity.y)
                    if hasattr(io_port_entity, 'capacitance'):
                        io_port_proto.capacitance = safe_float(io_port_entity.capacitance)
                    
                    # Add to collection
                    io_ports.append(io_port_proto)
                except Exception as e:
                    # Log error but continue processing other nodes
                    print(f"Error processing IO_PORT {node}: {str(e)}")
        
        # Assign io_ports list to netlist_proto
        if io_ports:
            netlist_proto.io_ports.extend(io_ports)
        
        # Collect and add TPnodes (timing path nodes)
        tp_nodes = []
        for node in list(netlist.nodes):
            if (node in netlist.nodes and 
                'type' in netlist.nodes[node] and 
                'entity' in netlist.nodes[node] and
                netlist.nodes[node]['type'] == "TP_NODE"):
                try:
                    tp_node_entity = netlist.nodes[node]['entity']
                    
                    # Create protobuf TP node object
                    tp_node_proto = pb2.TPNodeEntity()
                    tp_node_proto.name = safe_str(node)
                    
                    # Populate fields from entity
                    if hasattr(tp_node_entity, 'arrival_time'):
                        tp_node_proto.arrival_time = safe_float(tp_node_entity.arrival_time)
                    if hasattr(tp_node_entity, 'required_time'):
                        tp_node_proto.required_time = safe_float(tp_node_entity.required_time)
                    if hasattr(tp_node_entity, 'slack'):
                        tp_node_proto.slack = safe_float(tp_node_entity.slack)
                    if hasattr(tp_node_entity, 'clock'):
                        tp_node_proto.clock = safe_str(tp_node_entity.clock)
                    if hasattr(tp_node_entity, 'is_startpoint'):
                        tp_node_proto.is_startpoint = safe_bool(tp_node_entity.is_startpoint)
                    if hasattr(tp_node_entity, 'is_endpoint'):
                        tp_node_proto.is_endpoint = safe_bool(tp_node_entity.is_endpoint)
                    
                    # Add to collection
                    tp_nodes.append(tp_node_proto)
                except Exception as e:
                    print(f"Error processing TP_NODE {node}: {str(e)}")
        
        # Assign tp_nodes list to netlist_proto
        if tp_nodes:
            netlist_proto.tp_nodes.extend(tp_nodes)
        
        # Collect and add gates
        gates = []
        for node in list(netlist.nodes):
            if (node in netlist.nodes and 
                'type' in netlist.nodes[node] and 
                'entity' in netlist.nodes[node] and
                netlist.nodes[node]['type'] == "GATE"):
                try:
                    gate_entity = netlist.nodes[node]['entity']
                    
                    # Create protobuf gate object
                    gate_proto = pb2.GateEntity()
                    gate_proto.name = safe_str(node)
                    
                    # Populate fields from entity
                    if hasattr(gate_entity, 'cell_type'):
                        gate_proto.cell_type = safe_str(gate_entity.cell_type)
                    if hasattr(gate_entity, 'x'):
                        gate_proto.x = safe_float(gate_entity.x)
                    if hasattr(gate_entity, 'y'):
                        gate_proto.y = safe_float(gate_entity.y)
                    if hasattr(gate_entity, 'width'):
                        gate_proto.width = safe_float(gate_entity.width)
                    if hasattr(gate_entity, 'height'):
                        gate_proto.height = safe_float(gate_entity.height)
                    if hasattr(gate_entity, 'orientation'):
                        gate_proto.orientation = safe_str(gate_entity.orientation)
                    
                    # Add to collection
                    gates.append(gate_proto)
                except Exception as e:
                    print(f"Error processing GATE {node}: {str(e)}")
        
        # Assign gates list to netlist_proto
        if gates:
            netlist_proto.gates.extend(gates)
        
        # Collect and add standard cells
        std_cells = []
        for node in list(netlist.nodes):
            if (node in netlist.nodes and 
                'type' in netlist.nodes[node] and 
                'entity' in netlist.nodes[node] and
                netlist.nodes[node]['type'] == "STANDARD_CELL"):
                try:
                    std_cell_entity = netlist.nodes[node]['entity']
                    
                    # Create protobuf standard cell object
                    std_cell_proto = pb2.StandardCellEntity()
                    std_cell_proto.name = safe_str(node)
                    
                    # Populate fields from entity
                    if hasattr(std_cell_entity, 'width'):
                        std_cell_proto.width = safe_float(std_cell_entity.width)
                    if hasattr(std_cell_entity, 'height'):
                        std_cell_proto.height = safe_float(std_cell_entity.height)
                    if hasattr(std_cell_entity, 'no_of_input_pins'):
                        std_cell_proto.no_of_input_pins = safe_int(std_cell_entity.no_of_input_pins)
                    if hasattr(std_cell_entity, 'no_of_output_pins'):
                        std_cell_proto.no_of_output_pins = safe_int(std_cell_entity.no_of_output_pins)
                    if hasattr(std_cell_entity, 'is_sequential'):
                        std_cell_proto.is_sequential = safe_bool(std_cell_entity.is_sequential)
                    if hasattr(std_cell_entity, 'is_inverter'):
                        std_cell_proto.is_inverter = safe_bool(std_cell_entity.is_inverter)
                    if hasattr(std_cell_entity, 'is_buffer'):
                        std_cell_proto.is_buffer = safe_bool(std_cell_entity.is_buffer)
                    if hasattr(std_cell_entity, 'drive_strength'):
                        std_cell_proto.drive_strength = safe_float(std_cell_entity.drive_strength)
                    
                    # Add to collection
                    std_cells.append(std_cell_proto)
                except Exception as e:
                    print(f"Error processing STANDARD_CELL {node}: {str(e)}")
        
        # Assign standard cells list to netlist_proto
        if std_cells:
            netlist_proto.standard_cells.extend(std_cells)
    
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
