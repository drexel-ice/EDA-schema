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
    
    # Helper functions for safe type conversions
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
    
    # Map type names to converter functions
    converters = {
        'float': safe_float,
        'int': safe_int,
        'str': safe_str,
        'bool': safe_bool
    }
    
    # Define schema mappings
    schema = {
        # Top-level properties
        'basic_fields': {
            'width': {'type': 'float'},
            'height': {'type': 'float'},
            'no_of_inputs': {'type': 'int'},
            'no_of_outputs': {'type': 'int'},
            'utilization': {'type': 'float'},
            'cell_density': {'type': 'float'},
            'pin_density': {'type': 'float'},
            'net_density': {'type': 'float'}
        },
        # Nested objects with their fields
        'nested_objects': {
            'cell_metrics': {
                'no_of_combinational_cells': {'type': 'int'},
                'no_of_sequential_cells': {'type': 'int'},
                'no_of_buffers': {'type': 'int'},
                'no_of_inverters': {'type': 'int'},
                'no_of_fillers': {'type': 'int'},
                'no_of_tap_cells': {'type': 'int'},
                'no_of_diodes': {'type': 'int'},
                'no_of_macros': {'type': 'int'},
                'no_of_total_cells': {'type': 'int'}
            },
            'area_metrics': {
                'combinational_cell_area': {'type': 'float'},
                'sequential_cell_area': {'type': 'float'},
                'buffer_area': {'type': 'float'},
                'inverter_area': {'type': 'float'},
                'filler_area': {'type': 'float'},
                'tap_cell_area': {'type': 'float'},
                'diode_area': {'type': 'float'},
                'macro_area': {'type': 'float'},
                'cell_area': {'type': 'float'},
                'total_area': {'type': 'float'}
            },
            'power_metrics': {
                'combinational_power': {'type': 'float'},
                'sequential_power': {'type': 'float'},
                'macro_power': {'type': 'float'},
                'internal_power': {'type': 'float'},
                'switching_power': {'type': 'float'},
                'leakage_power': {'type': 'float'},
                'total_power': {'type': 'float'}
            },
            'critical_path_metrics': {
                'startpoint': {'type': 'str'},
                'endpoint': {'type': 'str'},
                'worst_arrival_time': {'type': 'float'},
                'worst_slack': {'type': 'float'},
                'total_negative_slack': {'type': 'float'},
                'no_of_timing_paths': {'type': 'int'},
                'no_of_slack_violations': {'type': 'int'}
            }
        },
        # Dictionary defining node types and their field mappings
        'node_types': {
            'IO_PORT': {
                'direction': {'type': 'str'},
                'x': {'type': 'float'},
                'y': {'type': 'float'},
                'capacitance': {'type': 'float'}
            },
            'TP_NODE': {
                'arrival_time': {'type': 'float'},
                'required_time': {'type': 'float'},
                'slack': {'type': 'float'},
                'clock': {'type': 'str'},
                'is_startpoint': {'type': 'bool'},
                'is_endpoint': {'type': 'bool'}
            },
            'GATE': {
                'cell_type': {'type': 'str'},
                'x': {'type': 'float'},
                'y': {'type': 'float'},
                'width': {'type': 'float'},
                'height': {'type': 'float'},
                'orientation': {'type': 'str'}
            },
            'STANDARD_CELL': {
                'width': {'type': 'float'},
                'height': {'type': 'float'},
                'no_of_input_pins': {'type': 'int'},
                'no_of_output_pins': {'type': 'int'},
                'is_sequential': {'type': 'bool'},
                'is_inverter': {'type': 'bool'},
                'is_buffer': {'type': 'bool'},
                'drive_strength': {'type': 'float'}
            }
        },
        # Path field mappings
        'timing_path_fields': {
            'startpoint': {'type': 'str'},
            'endpoint': {'type': 'str'},
            'path_type': {'type': 'str'},
            'arrival_time': {'type': 'float'},
            'required_time': {'type': 'float'},
            'slack': {'type': 'float'},
            'no_of_gates': {'type': 'int'},
            'is_critical_path': {'type': 'bool'}
        }
    }
    
    # Process basic fields
    for field, field_info in schema['basic_fields'].items():
        if hasattr(netlist, field):
            value = getattr(netlist, field)
            if value is not None:
                converter = converters[field_info['type']]
                setattr(netlist_proto, field, converter(value))
    
    # Process nested objects
    for obj_name, obj_fields in schema['nested_objects'].items():
        if hasattr(netlist, obj_name):
            obj = getattr(netlist, obj_name)
            if obj is not None:
                for field, field_info in obj_fields.items():
                    if hasattr(obj, field):
                        value = getattr(obj, field)
                        if value is not None:
                            converter = converters[field_info['type']]
                            setattr(getattr(netlist_proto, obj_name), field, converter(value))
    
    # Process timing paths
    if hasattr(netlist, 'timing_paths'):
        for path_type, paths in netlist.timing_paths.items():
            for path in paths:
                path_proto = netlist_proto.timing_paths.add()
                for field, field_info in schema['timing_path_fields'].items():
                    if field in path:
                        converter = converters[field_info['type']]
                        setattr(path_proto, field, converter(path[field]))
    
    # Process nodes by type
    if hasattr(netlist, 'nodes'):
        # Create a mapping from node types to protobuf field names and creation functions
        # Only include node types that have corresponding protobuf classes
        node_type_mapping = {}
        
        # Safely add node type mappings only if the protobuf class exists
        if hasattr(pb2, 'IOPortEntity'):
            node_type_mapping['IO_PORT'] = ('io_ports', pb2.IOPortEntity)
            
        # TPNodeEntity doesn't exist in eda_schema_pb2, so we'll skip it
        # if hasattr(pb2, 'TPNodeEntity'):
        #     node_type_mapping['TP_NODE'] = ('tp_nodes', pb2.TPNodeEntity)
        
        if hasattr(pb2, 'GateEntity'):
            node_type_mapping['GATE'] = ('gates', pb2.GateEntity)
            
        if hasattr(pb2, 'StandardCellEntity'):
            node_type_mapping['STANDARD_CELL'] = ('standard_cells', pb2.StandardCellEntity)
        
        # Group nodes by type
        nodes_by_type = {}
        for node_name, node_data in netlist.nodes.items():
            if 'type' in node_data and 'entity' in node_data:
                node_type = node_data['type']
                if node_type in node_type_mapping:
                    if node_type not in nodes_by_type:
                        nodes_by_type[node_type] = []
                    nodes_by_type[node_type].append((node_name, node_data['entity']))
        
        # Process each node type group
        for node_type, proto_info in node_type_mapping.items():
            if node_type in nodes_by_type:
                proto_field_name, proto_class = proto_info
                proto_objects = []
                
                for node_name, entity in nodes_by_type[node_type]:
                    try:
                        # Create a new protobuf object for this node
                        proto_obj = proto_class()
                        proto_obj.name = safe_str(node_name)
                        
                        # Apply field schema
                        for field, field_info in schema['node_types'][node_type].items():
                            if hasattr(entity, field):
                                value = getattr(entity, field)
                                if value is not None:
                                    converter = converters[field_info['type']]
                                    setattr(proto_obj, field, converter(value))
                        
                        proto_objects.append(proto_obj)
                    except Exception as e:
                        print(f"Error processing {node_type} {node_name}: {str(e)}")
                
                # Add all objects of this type to the appropriate protobuf field
                if proto_objects:
                    getattr(netlist_proto, proto_field_name).extend(proto_objects)
    
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
