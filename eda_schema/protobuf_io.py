"""
This module provides functions to load and save EDA-schema entities from/to Protobuf files.

Changes:
- Updated `save_protobuf_file` to dynamically set fields based on the Protobuf `DESCRIPTOR` instead of hardcoding field assignments.
- Added `load_pb` function to directly load protobuf files into specific object types.
- Refactored type conversion utilities into module-level functions.
- Added schema-based approach for dataset_to_protobuf to improve maintainability.
- Added `protobuf_to_dataset` function to convert a protobuf object back into a Dataset object.
- Replaced hardcoded schema with dynamic schema generation from proto definitions.
"""

from google.protobuf.descriptor import FieldDescriptor

import eda_schema.eda_schema_pb2 as pb2
import eda_schema.entity as eda_schema_entity
from eda_schema.errors import ValidationError
from eda_schema.dataset import Dataset


FIELD_TYPE_MAP = {
    1: "float",   # TYPE_DOUBLE
    2: "float",   # TYPE_FLOAT
    3: "int",     # TYPE_INT64
    4: "int",     # TYPE_UINT64
    5: "int",     # TYPE_INT32
    6: "int",     # TYPE_FIXED64
    7: "int",     # TYPE_FIXED32
    8: "bool",    # TYPE_BOOL
    9: "string",  # TYPE_STRING
    # 10: "group",   # TYPE_GROUP (deprecated, rarely used)
    # 11: "message", # TYPE_MESSAGE
    # 12: "bytes",   # TYPE_BYTES
    13: "int",     # TYPE_UINT32
    # 14: "enum",    # TYPE_ENUM
    15: "int",     # TYPE_SFIXED32
    16: "int",     # TYPE_SFIXED64
    17: "int",     # TYPE_SINT32
    18: "int",     # TYPE_SINT64
}

# Type conversion utility functions - moved from inside dataset_to_protobuf to module level
# for reusability and better code organization. These can be used by other functions
# in the module that need safe type conversion.
def safe_float(value, default=0.0):
    """Convert a value to float with error handling.
    
    Args:
        value: Value to convert
        default: Default value to use if conversion fails
        
    Returns:
        float: Converted value or default
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
        
def safe_int(value, default=0):
    """Convert a value to int with error handling.
    
    Args:
        value: Value to convert
        default: Default value to use if conversion fails
        
    Returns:
        int: Converted value or default
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
        
def safe_str(value, default=""):
    """Convert a value to string with error handling.
    
    Args:
        value: Value to convert
        default: Default value to use if conversion fails
        
    Returns:
        str: Converted value or default
    """
    if value is None:
        return default
    return str(value)
        
def safe_bool(value, default=False):
    """Convert a value to bool with error handling.
    
    Args:
        value: Value to convert
        default: Default value to use if conversion fails
        
    Returns:
        bool: Converted value or default
    """
    if value is None:
        return default
    try:
        return bool(value)
    except (ValueError, TypeError):
        return default

# Mapping of field types to conversion functions
CONVERTER = {
    'float': safe_float,
    'int': safe_int,
    'string': safe_str,
    'bool': safe_bool
}

def eda_schema_to_protobuf(pb2_entity, edaschema_entity):
    """
    Convert an EDA-schema entity to a Protobuf object.

    Args:
        pb2_entity: An instance of the Protobuf message to populate.
        edaschema_entity: The EDA-schema entity containing source data.
    """
    # Loop through each field defined in the Protobuf descriptor
    for field in pb2_entity.DESCRIPTOR.fields:
        # Map Protobuf field type to a Python-friendly type name
        field_type = FIELD_TYPE_MAP.get(field.type)
        if not field_type:
            # Skip unsupported or complex types
            continue

        # Ensure the EDA-schema entity has the corresponding attribute
        try:
            assert hasattr(edaschema_entity, field.name)
        except AssertionError:
            print(f"Warning: {field.name} not found in EDA-schema entity {type(edaschema_entity).__name__}")
            raise ValidationError(f"Field {field.name} not found in EDA-schema entity {type(edaschema_entity).__name__}")

        # Get the value from the EDA-schema entity
        value = getattr(edaschema_entity, field.name)

        # Convert and assign the value if it's not None
        if value is not None:
            converter = CONVERTER[field_type]
            setattr(pb2_entity, field.name, converter(value))

def dataset_to_protobuf(dataset, netlist):
    """
    Converts a dataset and its associated netlist into a populated NetlistEntity protobuf message.

    Args:
        dataset: The full dataset object, used for accessing standard cell information.
        netlist: The netlist graph object containing nodes, edges, and related attributes.

    Returns:
        pb2.NetlistEntity: A fully populated NetlistEntity protobuf object representing the netlist structure.
    """
    # Create a new NetlistEntity protobuf message
    # This is the main protobuf message that will hold the netlist data
    netlist_proto = pb2.NetlistEntity()
    eda_schema_to_protobuf(netlist_proto, netlist)
    eda_schema_to_protobuf(netlist_proto.cell_metrics, netlist.cell_metrics)
    eda_schema_to_protobuf(netlist_proto.area_metrics, netlist.area_metrics)
    eda_schema_to_protobuf(netlist_proto.power_metrics, netlist.power_metrics)
    eda_schema_to_protobuf(netlist_proto.critical_path_metrics, netlist.critical_path_metrics)
    
    # NOTE: TimingPath → TimingPoint conversion is skipped for now.
    # TimingPoint is expected to be deprecated soon — consult with EDA-schema
    # before proceeding with this part of the conversion.
    for timing_path in netlist.timing_paths.values():
        timing_path_proto = netlist_proto.timing_paths.add()
        eda_schema_to_protobuf(timing_path_proto, timing_path[0])

    for clock_tree in netlist.clock_trees.values():
        clock_tree_proto = netlist_proto.clock_trees.add()
        eda_schema_to_protobuf(clock_tree_proto, clock_tree)


    for node in netlist:
        node_type = netlist.nodes[node]['type']
        node_entity = netlist.nodes[node]['entity']
        if node_type == 'IO_PORT':
            node_proto = netlist_proto.io_ports.add()
            eda_schema_to_protobuf(node_proto, node_entity)
        elif node_type == 'GATE':
            node_proto = netlist_proto.gates.add()
            standard_cell_entity = dataset.standard_cells[node_entity.standard_cell]
            eda_schema_to_protobuf(node_proto.standard_cell, standard_cell_entity)
            eda_schema_to_protobuf(node_proto, node_entity)
        elif node_type == 'INTERCONNECT':
            node_proto = stage_proto.netlist.nets.add()
            eda_schema_to_protobuf(node_proto, node_entity)

    for edge1, edge2 in netlist.edges:
        edge_proto = netlist_proto.edges.add()
        edge_proto.source = edge1
        edge_proto.target = edge2

    return netlist_proto

def protobuf_to_eda_schema(edaschema_entity, pb2_entity):
    """
    Convert an EDA-schema entity to a Protobuf object.

    Args:
        pb2_entity: An instance of the Protobuf message to populate.
        edaschema_entity: The EDA-schema entity containing source data.
    """
    data_dict = {}
    for field in pb2_entity.DESCRIPTOR.fields:
        field_type = FIELD_TYPE_MAP.get(field.type)
        if not field_type:
            # Skip unsupported or complex types
            continue
        value = getattr(pb2_entity, field.name)
        data_dict[field.name] = value
    edaschema_entity.load(data_dict)

def protobuf_to_dataset(netlist_proto):
    """
    Converts a protobuf object back into a Dataset object.

    Args:
        protobuf_obj: The protobuf object to convert.
        db_obj: The database object to associate with the Dataset.

    Returns:
        Dataset: The reconstructed Dataset object.
    """
    netlist_entity = eda_schema_entity.NetlistEntity()
    protobuf_to_eda_schema(netlist_entity, netlist_proto)

    netlist_entity.cell_metrics = eda_schema_entity.CellMetricsEntity()
    protobuf_to_eda_schema(netlist_entity.cell_metrics, netlist_proto.cell_metrics)

    netlist_entity.area_metrics = eda_schema_entity.AreaMetricsEntity()
    protobuf_to_eda_schema(netlist_entity.area_metrics, netlist_proto.area_metrics)

    netlist_entity.power_metrics = eda_schema_entity.PowerMetricsEntity()
    protobuf_to_eda_schema(netlist_entity.power_metrics, netlist_proto.power_metrics)

    netlist_entity.critical_path_metrics = eda_schema_entity.CriticalPathMetricsEntity()
    protobuf_to_eda_schema(netlist_entity.critical_path_metrics, netlist_proto.critical_path_metrics)

    for timing_path_proto in netlist_proto.timing_paths:
        timing_path = eda_schema_entity.TimingPathEntity()
        netlist_entity.timing_paths[(timing_path_proto.startpoint, timing_path_proto.endpoint, timing_path_proto.path_type)] = timing_path
        protobuf_to_eda_schema(timing_path, timing_path_proto)

    for io_port_proto in netlist_proto.io_ports:
        io_port_enity = eda_schema_entity.IOPortEntity()
        protobuf_to_eda_schema(io_port_enity, io_port_proto)
        netlist_entity.add_node(io_port_enity.name,
            type='IO_PORT',
            entity=io_port_enity,
        )
    for gate_proto in netlist_proto.gates:
        gate_enity = eda_schema_entity.GateEntity()
        gate_enity.standard_cell = gate_proto.standard_cell.name
        protobuf_to_eda_schema(gate_enity, gate_proto)
        netlist_entity.add_node(gate_enity.name,
            type='GATE',
            entity=gate_enity,
        )
    for interconnect_proto in netlist_proto.interconnects:
        interconnect_enity = eda_schema_entity.InterconnectEntity()
        protobuf_to_eda_schema(interconnect_enity, interconnect_proto)
        netlist_entity.add_node(interconnect_enity.name,
            type='INTERCONNECT',
            entity=interconnect_enity,
        )

    for edge in netlist_proto.edges:
        netlist_entity.add_edge(edge.source, edge.target)

    return netlist_entity

def load_protobuf_file(file_path):
    """
    Loads a NetlistEntity Protobuf message from a binary file.

    Args:
        file_path: Path to the file containing serialized NetlistEntity protobuf data.

    Returns:
        An instance of NetlistEntity.
    """
    netlist_proto = pb2.NetlistEntity()

    with open(file_path, "rb") as f:
        netlist_proto.ParseFromString(f.read())

    return netlist_proto

def save_protobuf_file(netlist_proto, file_path):
    """
    Serializes a Protobuf object and saves it to a binary file.

    Args:
        entity: A Protobuf message instance (e.g., NetlistEntity, CellMetricsEntity).
        file_path: Path where the serialized protobuf should be saved.
    """
    if netlist_proto is None:
        raise ValueError("Entity cannot be None.")

    if not hasattr(netlist_proto, 'SerializeToString'):
        raise TypeError("Provided entity is not a valid Protobuf message.")

    with open(file_path, "wb") as f:
        f.write(netlist_proto.SerializeToString())
