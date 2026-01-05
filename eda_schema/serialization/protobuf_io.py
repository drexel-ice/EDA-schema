"""
This module provides functions to load and save EDA-schema entities from/to Protobuf files.

Changes:
- Updated `save_protobuf_file` to dynamically set fields based on the Protobuf
  `DESCRIPTOR` instead of hardcoding field assignments.
- Added `load_pb` function to directly load protobuf files into specific object types.
- Refactored type conversion utilities into module-level functions.
- Added schema-based approach for dataset_to_protobuf to improve maintainability.
- Added `protobuf_to_dataset` function to convert a protobuf object back into a
  Dataset object.
- Replaced hardcoded schema with dynamic schema generation from proto definitions.
"""

from dataclasses import fields as dataclass_fields

from eda_schema.proto import eda_schema_pb2 as pb2
import eda_schema.entity as eda_schema_entity
from eda_schema.errors import ValidationError


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

        # Skip if the EDA-schema entity doesn't have the corresponding attribute
        if not hasattr(edaschema_entity, field.name):
            # Skip fields that don't exist in the entity (e.g., optional proto fields)
            continue

        # Get the value from the EDA-schema entity
        value = getattr(edaschema_entity, field.name)

        # Convert and assign the value if it's not None
        if value is not None:
            converter = CONVERTER[field_type]
            setattr(pb2_entity, field.name, converter(value))

def dataset_to_protobuf(_dataset, stage_entity):  # pylint: disable=too-many-branches
    """
    Converts a dataset and its associated netlist into a populated StageEntity protobuf message.

    Args:
        _dataset: The full dataset object (currently unused, kept for API compatibility).
        stage_entity: The design stage entity containing netlist and metrics.

    Returns:
        pb2.StageEntity: A fully populated StageEntity protobuf object.
    """
    # Create a new StageEntity protobuf message
    stage_proto = pb2.StageEntity()  # pylint: disable=no-member

    # Convert netlist
    if stage_entity.netlist:
        eda_schema_to_protobuf(stage_proto.netlist, stage_entity.netlist)

    # Convert metrics
    if stage_entity.cell_metrics:
        eda_schema_to_protobuf(stage_proto.cell_metrics, stage_entity.cell_metrics)
    if stage_entity.area_metrics:
        eda_schema_to_protobuf(stage_proto.area_metrics, stage_entity.area_metrics)
    if stage_entity.power_metrics:
        eda_schema_to_protobuf(stage_proto.power_metrics, stage_entity.power_metrics)
    if stage_entity.timing_metrics:
        eda_schema_to_protobuf(stage_proto.timing_metrics, stage_entity.timing_metrics)

    # Convert timing paths
    if stage_entity.netlist and stage_entity.netlist.timing_paths:
        for timing_path in stage_entity.netlist.timing_paths.values():
            timing_path_proto = stage_proto.netlist.timing_paths.add()
            eda_schema_to_protobuf(timing_path_proto, timing_path)

    # Convert clock trees
    if stage_entity.netlist and stage_entity.netlist.clock_trees:
        for clock_tree in stage_entity.netlist.clock_trees.values():
            clock_tree_proto = stage_proto.netlist.clock_trees.add()
            eda_schema_to_protobuf(clock_tree_proto, clock_tree)

    # Convert nodes
    if stage_entity.netlist:
        for node in stage_entity.netlist.nodes:
            node_type = stage_entity.netlist.nodes[node]['type']
            node_entity = stage_entity.netlist.nodes[node]['entity']
            if node_type == 'PORT':
                node_proto = stage_proto.netlist.ports.add()
                eda_schema_to_protobuf(node_proto, node_entity)
            elif node_type == 'GATE':
                node_proto = stage_proto.netlist.gates.add()
                # standard_cell is now a string in proto, not nested
                node_proto.standard_cell = node_entity.standard_cell
                eda_schema_to_protobuf(node_proto, node_entity)
            elif node_type == 'NET':
                node_proto = stage_proto.netlist.nets.add()
                eda_schema_to_protobuf(node_proto, node_entity)

    # Convert edges
    if stage_entity.netlist:
        for edge1, edge2 in stage_entity.netlist.edges:
            edge_proto = stage_proto.netlist.edges.add()
            edge_proto.source = edge1
            edge_proto.target = edge2

    return stage_proto

def _extract_proto_fields(pb2_entity):
    """
    Extract all fields from a Protobuf entity into a dictionary.

    Args:
        pb2_entity: An instance of the Protobuf message.

    Returns:
        dict: Dictionary of field names to values.
    """
    data_dict = {}
    for field in pb2_entity.DESCRIPTOR.fields:
        field_type = FIELD_TYPE_MAP.get(field.type)
        if not field_type:
            # Skip unsupported or complex types
            continue
        value = getattr(pb2_entity, field.name, None)
        # Include all values (including 0, False, empty string, None) for numeric/bool types
        # For strings, only include non-empty values
        if field_type in ('int', 'float', 'bool'):
            # Always include numeric and bool values, even if 0 or False
            data_dict[field.name] = value
        elif value:  # For strings and other types, only include if truthy
            data_dict[field.name] = value
    return data_dict

def protobuf_to_eda_schema(edaschema_entity, pb2_entity):
    """
    Convert a Protobuf object to an EDA-schema entity.

    Args:
        edaschema_entity: The EDA-schema entity to populate.
        pb2_entity: An instance of the Protobuf message containing source data.
    """

    data_dict = _extract_proto_fields(pb2_entity)

    # Filter out fields that don't exist in the entity's dataclass
    entity_field_names = {f.name for f in dataclass_fields(type(edaschema_entity))}
    filtered_dict = {k: v for k, v in data_dict.items() if k in entity_field_names}

    # Update the entity with the extracted fields
    for key, value in filtered_dict.items():
        if hasattr(edaschema_entity, key):
            setattr(edaschema_entity, key, value)

def protobuf_to_dataset(stage_proto):  # pylint: disable=too-many-branches
    """
    Converts a StageEntity protobuf object back into a DesignStageEntity object.

    Args:
        stage_proto: The StageEntity protobuf object to convert.

    Returns:
        DesignStageEntity: The reconstructed DesignStageEntity object.
    """
    # Extract required fields
    flow_id = stage_proto.netlist.flow_id if stage_proto.netlist else None
    stage = stage_proto.netlist.stage if stage_proto.netlist else None

    # Create netlist entity with required fields
    netlist_entity = eda_schema_entity.NetlistEntity(
        flow_id=flow_id or "",
        stage=stage or "",
        no_of_inputs=stage_proto.netlist.no_of_inputs if stage_proto.netlist else 0,
        no_of_outputs=stage_proto.netlist.no_of_outputs if stage_proto.netlist else 0,
        no_of_cells=stage_proto.netlist.no_of_cells if stage_proto.netlist else 0,
        no_of_nets=stage_proto.netlist.no_of_nets if stage_proto.netlist else 0,
        no_of_pins=stage_proto.netlist.no_of_pins if stage_proto.netlist else 0,
        utilization=stage_proto.netlist.utilization if stage_proto.netlist else 0.0,
    )

    # Load additional fields from proto
    if stage_proto.netlist:
        protobuf_to_eda_schema(netlist_entity, stage_proto.netlist)

    # Convert metrics - extract all fields first, then use load() to create entities
    if stage_proto.cell_metrics:
        cell_data = _extract_proto_fields(stage_proto.cell_metrics)
        # Ensure flow_id and stage are set
        cell_data.setdefault('flow_id', flow_id or "")
        cell_data.setdefault('stage', stage or "")
        netlist_entity.cell_metrics = eda_schema_entity.CellMetricsEntity.load(cell_data)

    if stage_proto.area_metrics:
        area_data = _extract_proto_fields(stage_proto.area_metrics)
        area_data.setdefault('flow_id', flow_id or "")
        area_data.setdefault('stage', stage or "")
        netlist_entity.area_metrics = eda_schema_entity.AreaMetricsEntity.load(area_data)

    if stage_proto.power_metrics:
        power_data = _extract_proto_fields(stage_proto.power_metrics)
        power_data.setdefault('flow_id', flow_id or "")
        power_data.setdefault('stage', stage or "")
        netlist_entity.power_metrics = eda_schema_entity.PowerMetricsEntity.load(power_data)

    if stage_proto.timing_metrics:
        timing_data = _extract_proto_fields(stage_proto.timing_metrics)
        timing_data.setdefault('flow_id', flow_id or "")
        timing_data.setdefault('stage', stage or "")
        netlist_entity.timing_metrics = eda_schema_entity.TimingMetricsEntity.load(timing_data)

    # Convert timing paths
    if stage_proto.netlist:
        for timing_path_proto in stage_proto.netlist.timing_paths:
            timing_path = eda_schema_entity.TimingPathEntity(
                flow_id=timing_path_proto.flow_id or flow_id or "",
                stage=timing_path_proto.stage or stage or "",
                startpoint=timing_path_proto.startpoint,
                endpoint=timing_path_proto.endpoint,
                path_type=timing_path_proto.path_type,
                arrival_time=timing_path_proto.arrival_time,
                required_time=timing_path_proto.required_time,
                slack=timing_path_proto.slack,
                no_of_pins=timing_path_proto.no_of_pins,
                is_critical_path=timing_path_proto.is_critical_path,
            )
            path_key = (
                timing_path_proto.startpoint,
                timing_path_proto.endpoint,
                timing_path_proto.path_type
            )
            netlist_entity.timing_paths[path_key] = timing_path
            protobuf_to_eda_schema(timing_path, timing_path_proto)

    # Convert ports
    if stage_proto.netlist:
        for port_proto in stage_proto.netlist.ports:
            port_entity = eda_schema_entity.PortEntity(
                flow_id=port_proto.flow_id or flow_id or "",
                stage=port_proto.stage or stage or "",
                name=port_proto.name,
                direction=port_proto.direction,
            )
            protobuf_to_eda_schema(port_entity, port_proto)
            netlist_entity.add_node(port_entity.name, type='PORT', entity=port_entity)

    # Convert gates
    if stage_proto.netlist:
        for gate_proto in stage_proto.netlist.gates:
            gate_entity = eda_schema_entity.GateEntity(
                flow_id=gate_proto.flow_id or flow_id or "",
                stage=gate_proto.stage or stage or "",
                name=gate_proto.name,
                standard_cell=gate_proto.standard_cell,  # Now a string
                no_of_inputs=gate_proto.no_of_inputs,
                no_of_outputs=gate_proto.no_of_outputs,
            )
            protobuf_to_eda_schema(gate_entity, gate_proto)
            netlist_entity.add_node(gate_entity.name, type='GATE', entity=gate_entity)

    # Convert nets
    if stage_proto.netlist:
        for net_proto in stage_proto.netlist.nets:
            net_entity = eda_schema_entity.NetEntity(
                flow_id=net_proto.flow_id or flow_id or "",
                stage=net_proto.stage or stage or "",
                name=net_proto.name,
                is_special_net=net_proto.is_special_net,
                no_of_fanouts=net_proto.no_of_fanouts,
            )
            protobuf_to_eda_schema(net_entity, net_proto)
            netlist_entity.add_node(net_entity.name, type='NET', entity=net_entity)

    # Convert edges
    if stage_proto.netlist:
        for edge in stage_proto.netlist.edges:
            netlist_entity.add_edge(edge.source, edge.target)

    # Create DesignStageEntity
    stage_entity = eda_schema_entity.DesignStageEntity(
        flow_id=flow_id or "",
        stage=stage or "",
        netlist=netlist_entity,
        cell_metrics=netlist_entity.cell_metrics,
        area_metrics=netlist_entity.area_metrics,
        power_metrics=netlist_entity.power_metrics,
        timing_metrics=netlist_entity.timing_metrics,
    )

    return stage_entity

def load_protobuf_file(file_path):
    """
    Loads a StageEntity Protobuf message from a binary file.

    Args:
        file_path: Path to the file containing serialized StageEntity protobuf data.

    Returns:
        An instance of StageEntity.
    """
    stage_proto = pb2.StageEntity()  # pylint: disable=no-member

    with open(file_path, "rb") as f:
        stage_proto.ParseFromString(f.read())

    return stage_proto

def save_protobuf_file(proto_entity, file_path):
    """
    Serializes a Protobuf object and saves it to a binary file.

    Args:
        proto_entity: A Protobuf message instance (e.g., StageEntity, NetlistEntity).
        file_path: Path where the serialized protobuf should be saved.
    """
    if proto_entity is None:
        raise ValueError("Entity cannot be None.")

    if not hasattr(proto_entity, 'SerializeToString'):
        raise TypeError("Provided entity is not a valid Protobuf message.")

    with open(file_path, "wb") as f:
        f.write(proto_entity.SerializeToString())
