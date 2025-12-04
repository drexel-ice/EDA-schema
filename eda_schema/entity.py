from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from pydantic import Field

from eda_schema.base import BaseEntity, GraphEntity, Image2D


class DesignStages(str, Enum):
    """
    Enumeration of all major stages in a physical design flow.
    Each stage corresponds to a key milestone in the ASIC layout process
    and may be associated with metrics, constraints, and intermediate data.
    """
    FLOORPLAN      = "floorplan"
    GLOBAL_PLACE   = "global_place"
    PLACE_RESIZED  = "place_resized"
    DETAILED_PLACE = "detailed_place"
    CTS            = "cts"
    GLOBAL_ROUTE   = "global_route"
    DETAILED_ROUTE = "detailed_route"
    FINAL          = "final"


class DesignFlowEntity(BaseEntity):
    """Top-level container for a design flow and its stages."""

    flow_id: str = Field(description="Primary key for the flow", metadata={"pk": True})

    design: str
    run_status: Optional[str] = None
    datetime: Optional[str] = None
    runtime: Optional[timedelta] = None

    constraints: Optional["ConstraintEntity"] = None
    stages: Dict[str, "DesignStageEntity"] = Field(default_factory=dict)


class ConstraintEntity(BaseEntity):
    """Timing, electrical, routing, and IO constraints applied to a design."""

    flow_id: str = Field(description="Primary key for the flow", metadata={"pk": True})

    # Clock-related
    clock_period: Optional[float] = None
    clock_uncertainty: Optional[float] = None
    clock_latency: Optional[float] = None
    clock_transition: Optional[float] = None

    # IO constraints
    input_delay: Optional[float] = None
    output_delay: Optional[float] = None

    aspect_ratio: Optional[float] = None
    core_utilization: Optional[float] = None


class DesignStageEntity(BaseEntity):
    """Metadata and metrics for a single stage in the design flow."""

    flow_id: str = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: str = Field(metadata={"pk": True})

    run_status: Optional[str] = None
    runtime: Optional[timedelta] = None

    netlist: Optional["NetlistEntity"] = None
    cell_metrics: Optional["CellMetricsEntity"] = None
    area_metrics: Optional["AreaMetricsEntity"] = None
    power_metrics: Optional["PowerMetricsEntity"] = None
    timing_metrics: Optional["TimingMetricsEntity"] = None
    routability_metrics: Optional["RoutabilityMetricsEntity"] = None


class CellMetricsEntity(BaseEntity):
    """Counts of various cell categories in the design."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})

    no_of_combinational_cells: int
    no_of_sequential_cells: int
    no_of_buffers: int
    no_of_inverters: int
    no_of_fillers: int
    no_of_tap_cells: int
    no_of_diodes: int
    no_of_macros: int
    no_of_total_cells: int


class AreaMetricsEntity(BaseEntity):
    """Area metrics for cells, macros, die, and core."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})

    combinational_cell_area: float
    sequential_cell_area: float
    buffer_area: float
    inverter_area: float
    filler_area: float
    tap_cell_area: float
    diode_area: float
    macro_area: float

    cell_area: float
    total_area: float


class PowerMetricsEntity(BaseEntity):
    """Aggregated internal, switching, leakage, and total power metrics."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})

    combinational_power: float
    sequential_power: float
    macro_power: float
    internal_power: float
    switching_power: float
    leakage_power: float
    total_power: float


class TimingMetricsEntity(BaseEntity):
    """Top-level summary of timing slack and critical path statistics."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})

    total_negative_slack: float
    worst_slack: float

    critical_path_startpoint: str
    critical_path_endpoint: str
    worst_arrival_time: float
    worst_required_time: float

    no_of_endpoints: int
    no_of_violating_endpoints: int


class RoutabilityMetricsEntity(BaseEntity):
    """Routability and congestion metrics (overflow, congestion maps, layer usage)."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})

    # Rudy-based congestion images
    rudy_net: Optional[Image2D] = None
    rudy_net_long: Optional[Image2D] = None
    rudy_net_short: Optional[Image2D] = None
    rudy_pin: Optional[Image2D] = None
    rudy_pin_long: Optional[Image2D] = None
    rudy_pin_short: Optional[Image2D] = None

    # # Scalar summary metrics
    # total_resource: Optional[float] = None
    # total_demand: Optional[float] = None
    # total_overflow: Optional[float] = None
    # total_overflow_h: Optional[float] = None
    # total_overflow_v: Optional[float] = None
    # total_usage_percent: Optional[float] = None

    # # Per-metal-layer metrics
    # total_resource_by_metal_layers: Optional[Dict[str, float]] = None
    # total_demand_by_metal_layers: Optional[Dict[str, float]] = None
    # total_overflow_by_metal_layers: Optional[Dict[str, float]] = None
    # total_overflow_h_by_metal_layers: Optional[Dict[str, float]] = None
    # total_overflow_v_by_metal_layers: Optional[Dict[str, float]] = None
    # total_usage_percent_by_metal_layers: Optional[Dict[str, float]] = None

    # # Congestion heatmaps (images)
    # horizontal_congestion: Optional[Any] = None
    # vertical_congestion: Optional[Any] = None
    # total_congestion: Optional[Any] = None

    # # Density maps (all images)
    # pin_density: Optional[Any] = None
    # net_density: Optional[Any] = None
    # cell_density: Optional[Any] = None
    # drv_locations: Optional[Any] = None

    # # Simple int field
    # no_of_drvs: Optional[int] = None



class PortEntity(BaseEntity):
    """Named input/output port and its physical + electrical attributes."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    name: str = Field(metadata={"pk": True})

    direction: str

    x: Optional[float] = None
    y: Optional[float] = None


class GateEntity(BaseEntity):
    """Placed gate instance, including physical bounds and pin counts."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    name: str = Field(metadata={"pk": True})

    standard_cell: str

    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None

    no_of_inputs: int
    no_of_outputs: int


class StandardCellEntity(BaseEntity):
    """Standard-cell library definition and its electrical characteristics."""

    name: str = Field(metadata={"pk": True})
    width: float
    height: float

    no_of_input_pins: int
    no_of_output_pins: int

    is_sequential: bool
    is_inverter: bool
    is_buffer: bool
    is_filler: bool
    is_diode: bool

    drive_strength: Optional[int] = None

    input_capacitance_min: Optional[float] = None
    input_capacitance_max: Optional[float] = None

    output_capacitance_min: Optional[float] = None
    output_capacitance_max: Optional[float] = None

    leakage_power_min: Optional[float] = None
    leakage_power_max: Optional[float] = None


class PinEntity(BaseEntity):
    """Pin instance with timing and electrical details."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    name: str = Field(metadata={"pk": True})

    direction: str

    is_startpoint: bool
    is_endpoint: bool

    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None

    setup_rise_slew: Optional[float] = None
    setup_fall_slew: Optional[float] = None
    hold_rise_slew: Optional[float] = None
    hold_fall_slew: Optional[float] = None

    setup_rise_slack: Optional[float] = None
    setup_fall_slack: Optional[float] = None
    hold_rise_slack: Optional[float] = None
    hold_fall_slack: Optional[float] = None

    load_capacitance: Optional[float] = None
    switching_activity: Optional[float] = None


class MetalSegmentEntity(BaseEntity):
    """Single metal routing segment with coordinates and properties."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    net_name: Optional[str] = Field(metadata={"pk": True})
    name: str = Field(metadata={"pk": True})

    metal_layer: str

    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None

    x: Optional[float] = None
    y: Optional[float] = None

    length: Optional[float] = None
    resistance: Optional[float] = None
    capacitance: Optional[float] = None
    rudy: Optional[float] = None


class ViaEntity(BaseEntity):
    """Via connecting routing layers at a physical coordinate."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    net_name: Optional[str] = Field(metadata={"pk": True})

    via_layer: str

    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None


class NetEntity(GraphEntity):
    """Represents a routed net, including metal segments and vias."""

    NODE_TYPES: ClassVar[Dict[str, type]] = {
        "METALSEGMENT": MetalSegmentEntity,
        "VIA": ViaEntity,
    }

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    name: str = Field(metadata={"pk": True})

    is_special_net: bool
    no_of_fanouts: int

    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None

    length: Optional[float] = None
    hpwl: Optional[float] = None
    resistance: Optional[float] = None
    capacitance: Optional[float] = None
    total_coupling_capacitance: Optional[float] = None


class NetlistEntity(GraphEntity):
    """Complete netlist with nodes, metrics, placement images, and timing data."""

    NODE_TYPES: ClassVar[Dict[str, type]] = {
        "GATE": GateEntity,
        "PORT": PortEntity,
        "PIN": PinEntity,
        "NET": NetEntity,
    }

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})

    width: Optional[float] = None
    height: Optional[float] = None

    no_of_inputs: int
    no_of_outputs: int
    no_of_cells: int
    no_of_nets: int
    no_of_pins: int
    utilization: float

    cell_placement: Optional[Image2D] = None
    cell_placement_combinational: Optional[Image2D] = None
    cell_placement_sequential: Optional[Image2D] = None
    cell_placement_filler: Optional[Image2D] = None
    pin_placement: Optional[Image2D] = None
    routing: Optional[Image2D] = None

    routing_by_metal: Dict[str, Image2D] = Field(default_factory=dict)

    cell_metrics: Optional["CellMetricsEntity"] = None
    area_metrics: Optional["AreaMetricsEntity"] = None
    power_metrics: Optional["PowerMetricsEntity"] = None
    timing_metrics: Optional["TimingMetricsEntity"] = None

    timing_paths: Dict[Tuple[str, str, str], "TimingPathEntity"] = Field(default_factory=dict)
    clock_trees: Dict[str, "ClockTreeEntity"] = Field(default_factory=dict)
    power_delivery_network: Optional["PDNEntity"] = None


class ClockTreeEntity(GraphEntity):
    """Clock tree extracted from a netlist, including buffers and sinks."""

    NODE_TYPES: ClassVar[Dict[str, type]] = {
        "GATE": GateEntity,
        "PORT": PortEntity,
        "PIN":  PinEntity,
        "NET":  NetEntity,
    }

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    clock_source: str = Field(metadata={"pk": True})

    no_of_buffers: int = 0
    no_of_clock_sinks: int = 0

    cell_placement: Optional[Image2D] = None
    cell_placement_combinational: Optional[Image2D] = None
    cell_placement_sequential: Optional[Image2D] = None
    pin_placement: Optional[Image2D] = None
    routing: Optional[Image2D] = None

    routing_by_metal: Dict[str, Image2D] = Field(default_factory=dict)

    def load_from_netlist(self, netlist, clock_source: str, dff_cells: List[str]):
        """
        Extract the clock tree from a full design netlist.

        This performs a directed traversal starting from the specified
        `clock_source` node and identifies all nodes reachable along the
        clock distribution network. The resulting induced subgraph is then
        stored in `self._graph`.

        Args:
            netlist (GraphEntity): The complete netlist to extract from.
            clock_source (str): Name of the root node of the clock tree.
            dff_cells (List[str]): List of standard-cell names that represent
                sequential elements (e.g., flip-flops). These nodes are counted
                as clock sinks and are not further traversed.
        """
        self.no_of_buffers = 0
        self.no_of_clock_sinks = 0
        self.clock_source = clock_source

        cts_nodes = self._traverse_cts(netlist, clock_source, dff_cells)
        self._graph = netlist.subgraph(cts_nodes).copy()

    def _traverse_cts(self, netlist, node: str, dff_cells: List[str]) -> List[str]:
        """
        Perform a DFS-style traversal to collect all clock distribution nodes.

        This helper identifies which nodes belong to the clock tree by
        recursively following outgoing edges until:
        - A flip-flop is reached (counted as a sink)
        - No further clock-propagating nodes are found

        Args:
            netlist (GraphEntity): Source netlist containing all nodes.
            node (str): Current node to evaluate.
            dff_cells (List[str]): Standard-cell names considered sequential.

        Returns:
            List[str]: Ordered list of nodes belonging to the clock tree.
        """
        traversed = [node]
        stack = [node]

        while stack:
            current = stack.pop()
            for out_node in netlist.successors(current):
                if out_node in traversed:
                    continue

                traversed.append(out_node)
                node_data = netlist.nodes[out_node]

                if (
                    node_data["type"] == "GATE"
                    and node_data["entity"].standard_cell in dff_cells
                ):
                    self.no_of_clock_sinks += 1
                    continue

                if node_data["type"] == "GATE":
                    self.no_of_buffers += 1

                stack.append(out_node)

        return traversed


class PDNEntity(BaseEntity):
    """Power distribution network: routing + IR drop + EM maps."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})

    routing_vdd: Optional[Image2D] = None
    routing_vss: Optional[Image2D] = None
    ir_drop_vdd: Optional[Image2D] = None
    ir_drop_vss: Optional[Image2D] = None
    em_vdd: Optional[Image2D] = None
    em_vss: Optional[Image2D] = None


class NetArcEntity(BaseEntity):
    """Timing arc across a routed net."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    startpoint: str = Field(metadata={"pk": True})
    endpoint: str = Field(metadata={"pk": True})
    path_type: str = Field(metadata={"pk": True})
    net_name: str = Field(metadata={"pk": True})

    delay: float
    arrival_time: float
    slew: float
    capacitance: Optional[float] = None


class CellArcEntity(BaseEntity):
    """Logical timing arc through a cell."""

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    startpoint: str = Field(metadata={"pk": True})
    endpoint: str = Field(metadata={"pk": True})
    path_type: str = Field(metadata={"pk": True})
    gate_name: str = Field(metadata={"pk": True})

    delay: float
    arrival_time: float
    slew: float


class TimingPathEntity(GraphEntity):
    """Detailed timing path composed of net arcs, cell arcs, and pin sequence."""

    NODE_TYPES: ClassVar[Dict[str, type]] = {
        "PIN": PinEntity,
        "PORT": PortEntity,
        "NET_ARC": NetArcEntity,
        "CELL_ARC": CellArcEntity,
    }

    flow_id: Optional[str] = Field(description="Primary key for the flow", metadata={"pk": True})
    stage: Optional[str] = Field(metadata={"pk": True})
    startpoint: str = Field(metadata={"pk": True})
    endpoint: str = Field(metadata={"pk": True})
    path_type: str = Field(metadata={"pk": True})

    arrival_time: float
    required_time: float
    slack: float

    no_of_pins: int
    is_critical_path: bool


class SchemaMetadata:
    """
    Central registry of Pydantic JSON-schema metadata for all EDA entities.

    This class provides:
      - A single source of truth for entity → schema mappings
      - Utility functions to retrieve schemas and iterate over them
      - Identification of which entities contain internal graphs
    """

    # ---------------------------------------------------------------
    # Primary registry mapping entity names → model classes
    # ---------------------------------------------------------------
    _ENTITY_MODELS: ClassVar[Dict[str, type]] = {
        "design_flows": DesignFlowEntity,
        "constraints": ConstraintEntity,
        "design_stages": DesignStageEntity,
        "netlists": NetlistEntity,
        "clock_trees": ClockTreeEntity,
        "power_delivery_networks": PDNEntity,
        "ports": PortEntity,
        "gates": GateEntity,
        "standard_cells": StandardCellEntity,
        "nets": NetEntity,
        "metal_segments": MetalSegmentEntity,
        "vias": ViaEntity,
        "pins": PinEntity,
        "timing_paths": TimingPathEntity,
        "net_arcs": NetArcEntity,
        "cell_arcs": CellArcEntity,
        "cell_metrics": CellMetricsEntity,
        "area_metrics": AreaMetricsEntity,
        "power_metrics": PowerMetricsEntity,
        "timing_metrics": TimingMetricsEntity,
        "routability_metrics": RoutabilityMetricsEntity,
    }

    _SCHEMAS: ClassVar[Dict[str, Dict[str, Any]]] = {
        name: model.model_json_schema().get("properties", {})
        for name, model in _ENTITY_MODELS.items()
    }

    _GRAPH_ENTITIES: ClassVar[List[str]] = [
        name
        for name, model in _ENTITY_MODELS.items()
        if issubclass(model, GraphEntity)
    ]

    @classmethod
    def items(cls) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Returns:
            List of (entity_name, schema_properties) tuples for all entities.
        """
        return list(cls._SCHEMAS.items())

    @classmethod
    def get_schema(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the JSON-schema of a specific entity.

        Args:
            name (str): Name of the entity (e.g., "nets", "timing_paths").

        Returns:
            dict | None: The schema properties, or None if not registered.
        """
        return cls._SCHEMAS.get(name)

    @classmethod
    def get_pk_columns(cls, entity_name: str) -> List[str]:
        """
        Return the list of primary-key fields for a given entity.

        Primary keys are detected via:
            Field(..., metadata={"pk": True})

        Args:
            entity_name (str): Name of the entity.

        Returns:
            List[str]: List of primary-key column names.
        """
        schema = cls.get_schema(entity_name)
        if schema is None:
            return []

        pk_cols = []
        for col_name, col_info in schema.items():
            meta = col_info.get("metadata", {})
            if meta.get("pk") is True:
                pk_cols.append(col_name)

        return pk_cols

    @classmethod
    def is_graph_entity(cls, entity_name: str) -> bool:
        """
        Check whether the specified entity is GraphEntity-based.

        Args:
            entity_name (str): The name of the entity to check.

        Returns:
            bool: True if the entity contains an internal directed graph.
        """
        return entity_name in cls._GRAPH_ENTITIES

# Rebuild all Pydantic models (resolve forward references)
for model in SchemaMetadata._ENTITY_MODELS.values():
    model.model_rebuild()
