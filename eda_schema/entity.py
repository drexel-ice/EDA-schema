# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/entity.py
# Authors :
#     Pratik Shrestha       <ps937@drexel.edu>
#
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike
# 4.0 International License (CC BY-NC-SA 4.0). You may obtain a copy of the
# license at: https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. Commercial use is
# expressly prohibited; derivative works must be shared under the same
# license terms (ShareAlike).

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import ClassVar, Dict, List, Optional, Tuple, Type

from eda_schema.base import BaseEntity, GraphEntity, Image2D

# ============================================================
# Design stages
# ============================================================


class DesignStages(str, Enum):
    """
    Enumeration of all major stages in a physical design flow.
    """

    FLOORPLAN = "floorplan"
    GLOBAL_PLACE = "global_place"
    PLACE_RESIZED = "place_resized"
    DETAILED_PLACE = "detailed_place"
    CTS = "cts"
    GLOBAL_ROUTE = "global_route"
    DETAILED_ROUTE = "detailed_route"
    FINAL = "final"

    @classmethod
    def tolist(cls):
        """
        Get a list of all stage values.

        Returns:
            list: List of stage string values.
        """
        return [stage.value for stage in cls]


# ============================================================
# Flow / constraint entities
# ============================================================


@dataclass(slots=True)
class DesignFlowEntity(BaseEntity):
    """Top-level container for a design flow and its stages."""

    flow_id: str = field(metadata={"pk": True})
    design: str
    run_status: Optional[str] = None

    constraints: Optional["ConstraintEntity"] = None
    stages: Dict[str, "DesignStageEntity"] = field(default_factory=dict)


@dataclass(slots=True)
class ConstraintEntity(BaseEntity):
    """Timing, electrical, routing, and IO constraints."""

    flow_id: str = field(metadata={"pk": True})

    clock_period: Optional[float] = None
    clock_uncertainty: Optional[float] = None
    clock_latency: Optional[float] = None
    clock_transition: Optional[float] = None

    input_delay: Optional[float] = None
    output_delay: Optional[float] = None

    aspect_ratio: Optional[float] = None
    core_utilization: Optional[float] = None


@dataclass(slots=True)
class DesignStageEntity(BaseEntity):
    """Metadata and metrics for a single design stage."""

    flow_id: str = field(metadata={"pk": True})
    stage: str = field(metadata={"pk": True})

    run_status: Optional[str] = None

    netlist: Optional["NetlistEntity"] = None
    cell_metrics: Optional["CellMetricsEntity"] = None
    area_metrics: Optional["AreaMetricsEntity"] = None
    power_metrics: Optional["PowerMetricsEntity"] = None
    timing_metrics: Optional["TimingMetricsEntity"] = None
    routability_metrics: Optional["RoutabilityMetricsEntity"] = None


# ============================================================
# Metrics entities
# ============================================================


@dataclass(slots=True)
class CellMetricsEntity(BaseEntity):
    """Counts of various cell categories."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})

    no_of_combinational_cells: int
    no_of_sequential_cells: int
    no_of_buffers: int
    no_of_inverters: int
    no_of_fillers: int
    no_of_tap_cells: int
    no_of_diodes: int
    no_of_macros: int
    no_of_total_cells: int


@dataclass(slots=True)
class AreaMetricsEntity(BaseEntity):
    """Area metrics for cells and die."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})

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


@dataclass(slots=True)
class PowerMetricsEntity(BaseEntity):
    """Aggregated power metrics."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})

    combinational_power: float
    sequential_power: float
    macro_power: float
    internal_power: float
    switching_power: float
    leakage_power: float
    total_power: float


@dataclass(slots=True)
class TimingMetricsEntity(BaseEntity):
    """Summary timing metrics."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})

    total_negative_slack: float
    worst_slack: float

    critical_path_startpoint: str
    critical_path_endpoint: str
    worst_arrival_time: float
    worst_required_time: float

    no_of_endpoints: int
    no_of_violating_endpoints: int


@dataclass(slots=True)
class RoutabilityMetricsEntity(BaseEntity):
    """Routability and congestion images."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})

    rudy_net: Optional[Image2D] = None
    rudy_net_long: Optional[Image2D] = None
    rudy_net_short: Optional[Image2D] = None
    rudy_pin: Optional[Image2D] = None


# ============================================================
# Physical entities
# ============================================================


@dataclass(slots=True)
class PortEntity(BaseEntity):
    """Named IO port."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})
    name: str = field(metadata={"pk": True})

    direction: str
    x: Optional[float] = None
    y: Optional[float] = None


@dataclass(slots=True)
class GateEntity(BaseEntity):
    """Placed gate instance."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})
    name: str = field(metadata={"pk": True})

    standard_cell: str
    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None

    no_of_inputs: int = 0
    no_of_outputs: int = 0

    internal_power: Optional[float] = None
    switching_power: Optional[float] = None
    leakage_power: Optional[float] = None
    total_power: Optional[float] = None

    ir_drop_vdd: Optional[float] = None
    ir_drop_vss: Optional[float] = None


@dataclass(slots=True)
class StandardCellEntity(BaseEntity):
    """Standard cell library entry."""

    name: str = field(metadata={"pk": True})
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


@dataclass(slots=True)
class PinEntity(BaseEntity):
    """Pin instance."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})
    name: str = field(metadata={"pk": True})

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


@dataclass(slots=True)
class NetEntity(BaseEntity):
    """Routed net."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})
    name: str = field(metadata={"pk": True})

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

    routing: Optional[Image2D] = None
    routing_by_metal: Dict[str, Image2D] = field(default_factory=dict)


@dataclass(slots=True)
class NetArcEntity(BaseEntity):
    """Timing arc across a routed net."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})
    startpoint: str = field(metadata={"pk": True})
    endpoint: str = field(metadata={"pk": True})
    path_type: str = field(metadata={"pk": True})
    net_name: str = field(metadata={"pk": True})

    delay: float = 0.0
    arrival_time: float = 0.0
    slew: float = 0.0
    capacitance: Optional[float] = None


@dataclass(slots=True)
class CellArcEntity(BaseEntity):
    """Logical timing arc through a cell."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})
    startpoint: str = field(metadata={"pk": True})
    endpoint: str = field(metadata={"pk": True})
    path_type: str = field(metadata={"pk": True})
    gate_name: str = field(metadata={"pk": True})

    delay: float = 0.0
    arrival_time: float = 0.0
    slew: float = 0.0


# ============================================================
# Graph-backed entities
# ============================================================


@dataclass(slots=True)
class NetlistEntity(GraphEntity):
    """Complete design netlist."""

    NODE_TYPES: ClassVar[Dict[str, Type[BaseEntity]]] = {
        "GATE": GateEntity,
        "PORT": PortEntity,
        "PIN": PinEntity,
        "NET": NetEntity,
    }

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})

    no_of_inputs: int
    no_of_outputs: int
    no_of_cells: int
    no_of_nets: int
    no_of_pins: int
    utilization: float

    width: Optional[float] = None
    height: Optional[float] = None
    total_wirelength: Optional[float] = None
    total_hpwl: Optional[float] = None

    cell_placement: Optional[Image2D] = None
    cell_placement_combinational: Optional[Image2D] = None
    cell_placement_sequential: Optional[Image2D] = None
    cell_placement_filler: Optional[Image2D] = None
    pin_placement: Optional[Image2D] = None
    routing: Optional[Image2D] = None
    routing_by_metal: Dict[str, Image2D] = field(default_factory=dict)

    cell_metrics: Optional["CellMetricsEntity"] = None
    area_metrics: Optional["AreaMetricsEntity"] = None
    power_metrics: Optional["PowerMetricsEntity"] = None
    timing_metrics: Optional["TimingMetricsEntity"] = None

    timing_paths: Dict[Tuple[str, str, str], "TimingPathEntity"] = field(
        default_factory=dict
    )
    clock_trees: Dict[str, "ClockTreeEntity"] = field(default_factory=dict)
    power_delivery_network: Optional["PDNEntity"] = None


@dataclass(slots=True)
class PDNEntity(BaseEntity):
    """Power distribution network: routing + IR drop + EM maps."""

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})

    routing_vdd: Optional[Image2D] = None
    routing_vss: Optional[Image2D] = None
    power_source: Optional[Image2D] = None
    ir_drop_vdd: Optional[Image2D] = None
    ir_drop_vss: Optional[Image2D] = None
    em_vdd: Optional[Image2D] = None
    em_vss: Optional[Image2D] = None


@dataclass(slots=True)
class ClockTreeEntity(GraphEntity):
    """
    Clock tree extracted from a netlist.

    Graph nodes/edges live in GraphEntity._graph. NODE_TYPES is used to validate
    node typing when you add nodes with (type=..., entity=...).
    """

    NODE_TYPES: ClassVar[Dict[str, Type[BaseEntity]]] = {
        "GATE": GateEntity,
        "PORT": PortEntity,
        "PIN": PinEntity,
        "NET": NetEntity,
    }

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})
    clock_source: str = field(metadata={"pk": True})

    no_of_buffers: int = 0
    no_of_clock_sinks: int = 0

    cell_placement: Optional[Image2D] = None
    cell_placement_combinational: Optional[Image2D] = None
    cell_placement_sequential: Optional[Image2D] = None
    pin_placement: Optional[Image2D] = None
    routing: Optional[Image2D] = None

    routing_by_metal: Dict[str, Image2D] = field(default_factory=dict)

    def load_from_netlist(
        self, netlist: GraphEntity, clock_source: str, dff_cells: List[str]
    ) -> None:
        """
        Extract a clock tree subgraph from a full netlist.

        Traverses fanout from clock_source until sequential sinks are reached.

        Args:
            netlist: Full netlist graph entity.
            clock_source: Starting node identifier for clock tree.
            dff_cells: List of sequential cell names to identify as sinks.
        """
        self.no_of_buffers = 0
        self.no_of_clock_sinks = 0
        self.clock_source = clock_source

        cts_nodes = self._traverse_cts(netlist, clock_source, dff_cells)
        self._graph = netlist.subgraph(cts_nodes).copy()

    def _traverse_cts(
        self, netlist: GraphEntity, node: str, dff_cells: List[str]
    ) -> List[str]:
        """
        Traverse reachable clock-distribution nodes.

        Counts:
          - buffers: gate nodes along the tree (excluding sequential sinks)
          - sinks: sequential gate nodes whose standard_cell is in dff_cells

        Args:
            netlist: Full netlist graph entity.
            node: Starting node identifier.
            dff_cells: List of sequential cell names to identify as sinks.

        Returns:
            list: List of traversed node identifiers.
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
                    node_data.get("type") == "GATE"
                    and node_data.get("entity") is not None
                    and getattr(node_data["entity"], "standard_cell", None) in dff_cells
                ):
                    self.no_of_clock_sinks += 1
                    continue

                if node_data.get("type") == "GATE":
                    self.no_of_buffers += 1

                stack.append(out_node)

        return traversed


@dataclass(slots=True)
class TimingPathEntity(GraphEntity):
    """Detailed timing path graph."""

    NODE_TYPES: ClassVar[Dict[str, Type[BaseEntity]]] = {
        "PIN": PinEntity,
        "PORT": PortEntity,
        "NET_ARC": NetArcEntity,
        "CELL_ARC": CellArcEntity,
    }

    flow_id: Optional[str] = field(metadata={"pk": True})
    stage: Optional[str] = field(metadata={"pk": True})
    startpoint: str = field(metadata={"pk": True})
    endpoint: str = field(metadata={"pk": True})
    path_type: str = field(metadata={"pk": True})

    arrival_time: float
    required_time: float
    slack: float

    no_of_pins: int
    is_critical_path: bool


# ============================================================
# Schema metadata (dataclass-based)
# ============================================================


class SchemaMetadata:
    """
    Central registry of all entity classes.

    This replaces the old Pydantic-based schema registry.
    """

    _ENTITY_MODELS: ClassVar[Dict[str, Type[BaseEntity]]] = {
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

    _GRAPH_ENTITIES: ClassVar[List[str]] = [
        name for name, cls in _ENTITY_MODELS.items() if issubclass(cls, GraphEntity)
    ]

    @classmethod
    def items(cls) -> List[Tuple[str, Type[BaseEntity]]]:
        """
        Get all entity name-class pairs.

        Returns:
            list: List of (entity_name, entity_class) tuples.
        """
        return list(cls._ENTITY_MODELS.items())

    @classmethod
    def get_columns(cls, entity_name: str) -> List[str]:
        """
        Get all column names for an entity.

        Args:
            entity_name: Name of the entity.

        Returns:
            list: List of field/column names.
        """
        model = cls._ENTITY_MODELS.get(entity_name)
        if model is None:
            return []
        return [f.name for f in fields(model)]

    @classmethod
    def get_pk_columns(cls, entity_name: str) -> List[str]:
        """
        Get primary key column names for an entity.

        Args:
            entity_name: Name of the entity.

        Returns:
            list: List of primary key field names.
        """
        model = cls._ENTITY_MODELS.get(entity_name)
        if model is None:
            return []
        return [f.name for f in fields(model) if f.metadata.get("pk") is True]

    @classmethod
    def is_graph_entity(cls, entity_name: str) -> bool:
        """
        Check if an entity is a graph entity.

        Args:
            entity_name: Name of the entity.

        Returns:
            bool: True if the entity is a graph entity, False otherwise.
        """
        return entity_name in cls._GRAPH_ENTITIES

    @classmethod
    def get_model(cls, name: str) -> Optional[Type]:
        """Return the entity class for a given name."""
        return cls._ENTITY_MODELS.get(name)

    @classmethod
    def get_fields(cls, name: str):
        """Return dataclass fields for an entity."""
        model = cls.get_model(name)
        if model is None:
            return None
        return fields(model)
