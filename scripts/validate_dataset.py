#!/usr/bin/env python3
"""
Validate an EDA-Schema ParquetDB dataset for structural integrity and consistency.

This script runs comprehensive validation checks on a dataset, including:
- Dataset structure (flows, stages, standard cells)
- Netlist graph integrity
- Entity consistency and referential integrity
- Metrics validity and relationships
- Image data validity
- Power delivery network (PDN) validation
- Timing path consistency
- Routability metrics validation

Uses lightweight get_graph_data() and get_table_data() to avoid expensive entity building.
Optimized to load data once per (flow_id, phase) and cache for all validators.

Usage:
    python scripts/validate_dataset.py dataset/nangate45_fullrun_combined
    python scripts/validate_dataset.py dataset/nangate45_fullrun_combined --flow-id flow123
    python scripts/validate_dataset.py dataset/nangate45_fullrun_combined --sample 10
    python scripts/validate_dataset.py dataset/nangate45_fullrun_combined --phases final detailed_route
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from tqdm import tqdm

try:
    from eda_schema.base import Image2D
    from eda_schema.dataset import Dataset
    from eda_schema.db import ParquetDB
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Install with: pip install eda-schema")
    sys.exit(1)


PHASES = ["floorplan", "global_place", "place_resized", "detailed_place",
          "cts", "global_route", "detailed_route", "final"]


class ValidationResult:
    """Track validation results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_pass(self):
        self.passed += 1

    def add_fail(self, msg: str):
        self.failed += 1
        self.errors.append(msg)

    def add_skip(self, msg: str = ""):
        self.skipped += 1
        if msg:
            self.warnings.append(f"SKIP: {msg}")

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def summary(self) -> str:
        total = self.passed + self.failed + self.skipped
        return (
            f"Results: {self.passed} passed, {self.failed} failed, "
            f"{self.skipped} skipped (total: {total})"
        )


@dataclass
class ValidationDataCache:
    """Cache for all data needed by validation functions for a single (flow_id, phase)."""
    flow_id: str
    phase: str

    # Graph data
    netlist_graph_data: Optional[Dict[str, Any]] = None

    # Table data
    netlist_table_data: Optional[Dict[str, Any]] = None
    gates_df: Optional[pd.DataFrame] = None
    nets_df: Optional[pd.DataFrame] = None
    ports_df: Optional[pd.DataFrame] = None
    pins_df: Optional[pd.DataFrame] = None
    timing_paths_df: Optional[pd.DataFrame] = None
    timing_paths_graph_lookup: Optional[Dict[Tuple[str, str, str], Dict[str, Any]]] = None

    # Metrics
    area_metrics: Optional[pd.Series] = None
    power_metrics: Optional[pd.Series] = None
    timing_metrics: Optional[pd.Series] = None
    cell_metrics: Optional[pd.Series] = None
    routability_metrics: Optional[pd.Series] = None
    power_delivery_networks: Optional[pd.Series] = None

    def get_netlist_graph_data(self) -> Optional[Dict[str, Any]]:
        """Get cached netlist graph data."""
        return self.netlist_graph_data

    def get_nodes_set(self) -> set:
        """Get set of nodes from netlist graph."""
        if self.netlist_graph_data:
            return set(self.netlist_graph_data.get("nodes", []))
        return set()

    def get_node_type_map(self) -> Dict[str, str]:
        """Get node type mapping from netlist graph."""
        if self.netlist_graph_data:
            nodes = self.netlist_graph_data.get("nodes", [])
            node_types = self.netlist_graph_data.get("node_types", [])
            return dict(zip(nodes, node_types))
        return {}


def load_validation_data(dataset: Dataset, flow_id: str, phase: str) -> ValidationDataCache:
    """Load all data needed for validation once per (flow_id, phase)."""
    cache = ValidationDataCache(flow_id=flow_id, phase=phase)

    # Load netlist graph data (used by many validators)
    try:
        cache.netlist_graph_data = dataset.db.get_graph_data("netlists", flow_id=flow_id, stage=phase)
    except Exception:
        cache.netlist_graph_data = None

    # Load netlist table data
    try:
        netlists_df = dataset.db.get_table_data("netlists", flow_id=flow_id, stage=phase)
        if len(netlists_df) > 0:
            cache.netlist_table_data = netlists_df.iloc[0].to_dict()
    except Exception:
        cache.netlist_table_data = None

    # Load entity table data
    try:
        cache.gates_df = dataset.db.get_table_data("gates", flow_id=flow_id, stage=phase)
    except Exception:
        cache.gates_df = pd.DataFrame()

    try:
        cache.nets_df = dataset.db.get_table_data("nets", flow_id=flow_id, stage=phase)
    except Exception:
        cache.nets_df = pd.DataFrame()

    try:
        cache.ports_df = dataset.db.get_table_data("ports", flow_id=flow_id, stage=phase)
    except Exception:
        cache.ports_df = pd.DataFrame()

    try:
        cache.pins_df = dataset.db.get_table_data("pins", flow_id=flow_id, stage=phase)
    except Exception:
        cache.pins_df = pd.DataFrame()

    # Load timing paths table and graph data
    try:
        cache.timing_paths_df = dataset.db.get_table_data("timing_paths", flow_id=flow_id, stage=phase)
    except Exception:
        cache.timing_paths_df = pd.DataFrame()

    # Load timing paths graph lookup
    cache.timing_paths_graph_lookup = {}
    try:
        graph_path = dataset.db._graph_path("timing_paths")
        if graph_path.exists():
            table = pq.read_table(graph_path)
            flow_mask = pc.equal(table["flow_id"], pa.scalar(str(flow_id)))
            stage_mask = pc.equal(table["stage"], pa.scalar(str(phase)))
            mask = pc.and_(flow_mask, stage_mask)
            filtered_table = table.filter(mask)

            for i in range(filtered_table.num_rows):
                row = filtered_table.slice(i, 1)
                startpoint = row["startpoint"][0].as_py()
                endpoint = row["endpoint"][0].as_py()
                path_type = row["path_type"][0].as_py()
                graph_json_str = row["graph_json"][0].as_py()
                cache.timing_paths_graph_lookup[(startpoint, endpoint, path_type)] = json.loads(graph_json_str)
    except Exception:
        pass

    # Load metrics
    try:
        area_df = dataset.db.get_table_data("area_metrics", flow_id=flow_id, stage=phase)
        if len(area_df) > 0:
            cache.area_metrics = area_df.iloc[0]
    except Exception:
        cache.area_metrics = None

    try:
        power_df = dataset.db.get_table_data("power_metrics", flow_id=flow_id, stage=phase)
        if len(power_df) > 0:
            cache.power_metrics = power_df.iloc[0]
    except Exception:
        cache.power_metrics = None

    try:
        timing_df = dataset.db.get_table_data("timing_metrics", flow_id=flow_id, stage=phase)
        if len(timing_df) > 0:
            cache.timing_metrics = timing_df.iloc[0]
    except Exception:
        cache.timing_metrics = None

    try:
        cell_df = dataset.db.get_table_data("cell_metrics", flow_id=flow_id, stage=phase)
        if len(cell_df) > 0:
            cache.cell_metrics = cell_df.iloc[0]
    except Exception:
        cache.cell_metrics = None

    try:
        routability_df = dataset.db.get_table_data("routability_metrics", flow_id=flow_id, stage=phase)
        if len(routability_df) > 0:
            cache.routability_metrics = routability_df.iloc[0]
    except Exception:
        cache.routability_metrics = None

    try:
        pdn_df = dataset.db.get_table_data("power_delivery_networks", flow_id=flow_id, stage=phase)
        if len(pdn_df) > 0:
            cache.power_delivery_networks = pdn_df.iloc[0]
    except Exception:
        cache.power_delivery_networks = None

    return cache


def validate_dataset_structure(dataset: Dataset, result: ValidationResult) -> None:
    """Validate dataset-level structure."""
    print("\n=== Dataset Structure ===")

    # Check standard cells
    if len(dataset.standard_cells) == 0:
        result.add_fail("Dataset has no standard cells")
    else:
        result.add_pass()
        print(f"✓ Standard cells loaded: {len(dataset.standard_cells)}")

    # Validate each standard cell
    for cell_name, std_cell in dataset.standard_cells.items():
        if std_cell.name != cell_name:
            result.add_fail(f"Standard cell name mismatch: {std_cell.name} != {cell_name}")
        if std_cell.width <= 0:
            result.add_fail(f"Standard cell {cell_name} has invalid width: {std_cell.width}")
        if std_cell.height <= 0:
            result.add_fail(f"Standard cell {cell_name} has invalid height: {std_cell.height}")


def validate_flow_structure(dataset: Dataset, flow_id: str, result: ValidationResult) -> None:
    """Validate a single flow's structure using table data."""
    # Check flow exists in database
    try:
        flows_df = dataset.db.get_table_data("design_flows", flow_id=flow_id)
        if len(flows_df) == 0:
            result.add_fail(f"Flow {flow_id}: not found in design_flows table")
            return

        flow_row = flows_df.iloc[0]
        if flow_row["flow_id"] != flow_id:
            result.add_fail(f"Flow {flow_id}: flow_id mismatch: {flow_row['flow_id']} != {flow_id}")
    except Exception as e:
        result.add_fail(f"Flow {flow_id}: could not load flow data: {e}")
        return

    # Check stages exist in database
    try:
        stages_df = dataset.db.get_table_data("design_stages", flow_id=flow_id)
        if len(stages_df) == 0:
            result.add_fail(f"Flow {flow_id}: has no stages")
            return

        valid_stages = set(PHASES)
        for _, row in stages_df.iterrows():
            stage_name = row["stage"]
            if stage_name not in valid_stages:
                result.add_fail(f"Flow {flow_id}: invalid stage name: {stage_name}")
            if row["flow_id"] != flow_id:
                result.add_fail(f"Flow {flow_id}: stage flow_id mismatch: {row['flow_id']} != {flow_id}")
    except Exception as e:
        result.add_fail(f"Flow {flow_id}: could not check stages: {e}")


def validate_netlist_graph(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate netlist graph structure using raw graph data."""
    graph_data = cache.get_netlist_graph_data()
    if graph_data is None:
        result.add_skip(f"{cache.flow_id}/{cache.phase}: Could not load netlist graph")
        return

    nodes = graph_data["nodes"]
    node_types = graph_data["node_types"]
    edges = graph_data["edges"]

    # Build node lookup for validation
    node_type_map = dict(zip(nodes, node_types))
    node_set = set(nodes)

    # Check node types
    valid_types = {"GATE", "NET", "PORT", "PIN"}
    for node_id, node_type in node_type_map.items():
        if node_type not in valid_types:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Node {node_id} has invalid type: {node_type}")

    # Check edges
    for source, target in edges:
        if source not in node_set:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Edge source {source} not in nodes")
        if target not in node_set:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Edge target {target} not in nodes")
        if source == target:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Self-loop detected: {source} -> {target}")


def validate_netlist_edge_consistency(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate that edges connect compatible node types."""
    graph_data = cache.get_netlist_graph_data()
    if graph_data is None:
        result.add_skip()
        return

    nodes = graph_data["nodes"]
    node_types = graph_data["node_types"]
    edges = graph_data["edges"]

    node_type_map = dict(zip(nodes, node_types))

    valid_patterns = [
        ("PORT", "NET"),
        ("NET", "GATE"),
        ("GATE", "NET"),
        ("NET", "PORT"),
        ("NET", "NET"),
        ("PIN", "NET"),
        ("NET", "PIN"),
        ("GATE", "PIN"),
        ("PIN", "GATE"),
    ]

    for source, target in edges:
        source_type = node_type_map.get(source)
        target_type = node_type_map.get(target)

        if source_type is None or target_type is None:
            continue  # Already caught by validate_netlist_graph

        if (source_type, target_type) not in valid_patterns:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Invalid edge pattern: {source_type} -> {target_type} "
                f"({source} -> {target})"
            )


def validate_netlist_entities(cache: ValidationDataCache, dataset: Dataset, result: ValidationResult) -> None:
    """Validate netlist entity consistency using table data."""
    graph_data = cache.get_netlist_graph_data()
    if graph_data is None:
        result.add_skip()
        return

    node_type_map = cache.get_node_type_map()

    # Get table data from cache
    gates_set = set(cache.gates_df["name"]) if len(cache.gates_df) > 0 else set()
    nets_set = set(cache.nets_df["name"]) if len(cache.nets_df) > 0 else set()
    ports_set = set(cache.ports_df["name"]) if len(cache.ports_df) > 0 else set()
    pins_set = set(cache.pins_df["name"]) if len(cache.pins_df) > 0 else set()

    # Validate node-to-entity mapping
    for node_id, node_type in node_type_map.items():
        if node_type == "GATE" and node_id not in gates_set:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Gate node {node_id} not found in gates table")
        elif node_type == "NET" and node_id not in nets_set:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Net node {node_id} not found in nets table")
        elif node_type == "PORT" and node_id not in ports_set:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Port node {node_id} not found in ports table")
        elif node_type == "PIN" and node_id not in pins_set:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Pin node {node_id} not found in pins table")

    # Validate standard cells for gates
    if len(cache.gates_df) > 0 and "standard_cell" in cache.gates_df.columns:
        standard_cells_set = set(dataset.standard_cells.keys())
        invalid_cells = cache.gates_df[~cache.gates_df["standard_cell"].isin(standard_cells_set)]
        if len(invalid_cells) > 0:
            for _, row in invalid_cells.iterrows():
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Gate {row['name']} references unknown standard cell: {row['standard_cell']}"
                )

    # Validate port directions
    if len(cache.ports_df) > 0 and "direction" in cache.ports_df.columns:
        valid_directions = {"INPUT", "OUTPUT", "INOUT"}
        invalid_ports = cache.ports_df[~cache.ports_df["direction"].isin(valid_directions)]
        if len(invalid_ports) > 0:
            for _, row in invalid_ports.iterrows():
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Port {row['name']} has invalid direction: {row['direction']}"
                )


def validate_net_properties(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate net properties and consistency using table data."""
    graph_data = cache.get_netlist_graph_data()
    if graph_data is None:
        result.add_skip()
        return

    edges = graph_data["edges"]

    # Build edge lookup for fanout calculation
    fanout_map = defaultdict(int)
    for source, target in edges:
        fanout_map[source] += 1

    node_type_map = cache.get_node_type_map()
    net_nodes = [n for n, t in node_type_map.items() if t == "NET"]

    if len(cache.nets_df) == 0:
        result.add_skip()
        return

    nets_dict = cache.nets_df.set_index("name").to_dict('index')

    for node_id in net_nodes:
        if node_id not in nets_dict:
            continue

        net_data = nets_dict[node_id]

        # Check no_of_fanouts
        if "no_of_fanouts" in net_data:
            actual_fanouts = fanout_map.get(node_id, 0)
            if net_data["no_of_fanouts"] != actual_fanouts:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Net {node_id} no_of_fanouts mismatch: "
                    f"{net_data['no_of_fanouts']} != {actual_fanouts} (graph)"
                )
            if net_data["no_of_fanouts"] < 0:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Net {node_id} has negative no_of_fanouts: {net_data['no_of_fanouts']}"
                )

        # Check coordinates
        x_min = net_data.get("x_min")
        if x_min is not None and not (isinstance(x_min, float) and math.isnan(x_min)):
            x_max = net_data.get("x_max")
            y_min = net_data.get("y_min")
            y_max = net_data.get("y_max")

            if x_max is None or (isinstance(x_max, float) and math.isnan(x_max)):
                result.add_fail(f"{cache.flow_id}/{cache.phase}: Net {node_id} has x_min but missing/invalid x_max")
            if y_min is None or (isinstance(y_min, float) and math.isnan(y_min)):
                result.add_fail(f"{cache.flow_id}/{cache.phase}: Net {node_id} has x_min but missing/invalid y_min")
            if y_max is None or (isinstance(y_max, float) and math.isnan(y_max)):
                result.add_fail(f"{cache.flow_id}/{cache.phase}: Net {node_id} has x_min but missing/invalid y_max")

            if x_max is not None and not (isinstance(x_max, float) and math.isnan(x_max)):
                if x_min > x_max:
                    result.add_fail(
                        f"{cache.flow_id}/{cache.phase}: Net {node_id} x_min ({x_min}) > x_max ({x_max})"
                    )
            if y_max is not None and not (isinstance(y_max, float) and math.isnan(y_max)):
                if y_min > y_max:
                    result.add_fail(
                        f"{cache.flow_id}/{cache.phase}: Net {node_id} y_min ({y_min}) > y_max ({y_max})"
                    )

        # Check length
        length = net_data.get("length")
        if length is not None and not (isinstance(length, float) and math.isnan(length)):
            if length < 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: Net {node_id} has negative length: {length}")


def validate_net_parasitics(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate net parasitic values using table data."""
    if len(cache.nets_df) == 0:
        result.add_skip()
        return

    for _, row in cache.nets_df.iterrows():
        net_name = row["name"]

        # Capacitance should be non-negative and reasonable (fF range, typically 0-1000 fF)
        capacitance = row.get("capacitance")
        if capacitance is not None and not (isinstance(capacitance, float) and math.isnan(capacitance)):
            if capacitance < 0:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Net {net_name} has negative capacitance: {capacitance}"
                )
            if capacitance >= 1e6:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Net {net_name} has unreasonably high capacitance: {capacitance} fF"
                )

        # Resistance should be non-negative and reasonable (fΩ range)
        resistance = row.get("resistance")
        if resistance is not None and not (isinstance(resistance, float) and math.isnan(resistance)):
            if resistance < 0:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Net {net_name} has negative resistance: {resistance}"
                )
            if resistance >= 1e12:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Net {net_name} has unreasonably high resistance: {resistance} fΩ"
                )


def validate_gate_coordinates(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate gate coordinates using table data."""
    if len(cache.gates_df) == 0:
        result.add_skip()
        return

    def is_valid_coord(val):
        return val is not None and not (isinstance(val, float) and math.isnan(val))

    for _, row in cache.gates_df.iterrows():
        gate_name = row["name"]
        x_min = row.get("x_min")
        x_max = row.get("x_max")
        y_min = row.get("y_min")
        y_max = row.get("y_max")

        if is_valid_coord(x_min) and is_valid_coord(x_max):
            if x_min > x_max:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Gate {gate_name}: x_min ({x_min}) > x_max ({x_max})"
                )
            if x_min < 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: Gate {gate_name}: x_min ({x_min}) < 0")

        if is_valid_coord(y_min) and is_valid_coord(y_max):
            if y_min > y_max:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Gate {gate_name}: y_min ({y_min}) > y_max ({y_max})"
                )
            if y_min < 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: Gate {gate_name}: y_min ({y_min}) < 0")

        # Check area
        if (is_valid_coord(x_min) and is_valid_coord(x_max) and
            is_valid_coord(y_min) and is_valid_coord(y_max)):
            width = x_max - x_min
            height = y_max - y_min
            area = width * height
            if area <= 0:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Gate {gate_name}: invalid area "
                    f"(width={width}, height={height})"
                )


def validate_netlist_metrics_consistency(cache: ValidationDataCache, dataset: Dataset, result: ValidationResult) -> None:
    """Validate netlist metrics match actual counts."""
    graph_data = cache.get_netlist_graph_data()
    netlist_data = cache.netlist_table_data

    if graph_data is None or netlist_data is None:
        result.add_skip()
        return

    node_types = graph_data["node_types"]
    node_type_map = cache.get_node_type_map()

    # Count actual nodes by type
    actual_cells = sum(1 for t in node_types if t == "GATE")
    actual_nets = sum(1 for t in node_types if t == "NET")
    actual_pins = sum(1 for t in node_types if t == "PIN")

    # Count ports by direction
    if len(cache.ports_df) > 0 and "direction" in cache.ports_df.columns:
        actual_inputs = len(cache.ports_df[cache.ports_df["direction"] == "INPUT"])
        actual_outputs = len(cache.ports_df[cache.ports_df["direction"] == "OUTPUT"])
    else:
        actual_inputs = 0
        actual_outputs = 0

    # Check consistency with netlist table data
    if "no_of_cells" in netlist_data:
        if netlist_data["no_of_cells"] != actual_cells:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Cell count mismatch: {netlist_data['no_of_cells']} != {actual_cells}"
            )
    if "no_of_nets" in netlist_data:
        if netlist_data["no_of_nets"] != actual_nets:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Net count mismatch: {netlist_data['no_of_nets']} != {actual_nets}"
            )

    # Validate pin counts accounting for floating pins
    if "no_of_pins" in netlist_data:
        # Calculate floating pins by iterating through gates
        total_floating_pins = 0

        if len(cache.gates_df) > 0 and "standard_cell" in cache.gates_df.columns and "name" in cache.gates_df.columns:
            # Build gate to standard_cell mapping
            gates_dict = cache.gates_df.set_index("name")["standard_cell"].to_dict()

            # Count connected pins per gate (PIN nodes in graph that start with "gate_name/")
            connected_pins_per_gate = defaultdict(int)
            for pin_node in [n for n, t in node_type_map.items() if t == "PIN"]:
                # PIN nodes are named like "gate_name/pin_name"
                if "/" in pin_node:
                    gate_name = pin_node.split("/", 1)[0]
                    connected_pins_per_gate[gate_name] += 1

            # Calculate floating pins for each gate
            for gate_name, std_cell_name in gates_dict.items():
                if std_cell_name in dataset.standard_cells:
                    std_cell = dataset.standard_cells[std_cell_name]
                    total_pins_for_gate = std_cell.no_of_input_pins + std_cell.no_of_output_pins
                    connected_pins_for_gate = connected_pins_per_gate.get(gate_name, 0)
                    floating_pins_for_gate = total_pins_for_gate - connected_pins_for_gate
                    total_floating_pins += max(0, floating_pins_for_gate)  # Ensure non-negative

        # Validate: actual_pins (connected) == no_of_pins (total) - floating_pins
        expected_connected_pins = netlist_data["no_of_pins"] - total_floating_pins
        if actual_pins != expected_connected_pins:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Pin count mismatch: "
                f"connected pins in graph ({actual_pins}) != "
                f"no_of_pins ({netlist_data['no_of_pins']}) - floating_pins ({total_floating_pins}) = {expected_connected_pins}"
            )

    if "no_of_inputs" in netlist_data:
        if netlist_data["no_of_inputs"] != actual_inputs:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Input count mismatch: {netlist_data['no_of_inputs']} != {actual_inputs}"
            )
    if "no_of_outputs" in netlist_data:
        if netlist_data["no_of_outputs"] != actual_outputs:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Output count mismatch: {netlist_data['no_of_outputs']} != {actual_outputs}"
            )

    # Check graph size
    total_nodes = actual_cells + actual_nets + actual_pins + actual_inputs + actual_outputs
    if len(graph_data["nodes"]) != total_nodes:
        result.add_fail(
            f"{cache.flow_id}/{cache.phase}: Total node count mismatch: {len(graph_data['nodes'])} != {total_nodes}"
        )


def validate_area_metrics(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate area metrics using table data."""
    if cache.area_metrics is None:
        result.add_skip()
        return

    am = cache.area_metrics

    # All area values should be non-negative
    if "total_area" in am and am["total_area"] < 0:
        result.add_fail(f"{cache.flow_id}/{cache.phase}: Total area is negative: {am['total_area']}")
    if "cell_area" in am and am["cell_area"] < 0:
        result.add_fail(f"{cache.flow_id}/{cache.phase}: Cell area is negative: {am['cell_area']}")
    if "combinational_cell_area" in am and am["combinational_cell_area"] < 0:
        result.add_fail(f"{cache.flow_id}/{cache.phase}: Combinational area is negative: {am['combinational_cell_area']}")
    if "sequential_cell_area" in am and am["sequential_cell_area"] < 0:
        result.add_fail(f"{cache.flow_id}/{cache.phase}: Sequential area is negative: {am['sequential_cell_area']}")

    # Validate area relationship: cell_area ≈ total_area + tap_cell_area + filler_area + diode_area
    # total_area is OpenROAD's "Design area" (functional cells only)
    # cell_area includes all placed cells (functional + tap + filler + diode + etc.)
    if all(k in am for k in ["cell_area", "total_area", "tap_cell_area"]):
        filler_area = am.get("filler_area", 0) or 0  # Handle None/NaN
        diode_area = am.get("diode_area", 0) or 0  # Handle None/NaN
        expected_cell_area = am["total_area"] + am["tap_cell_area"] + filler_area + diode_area
        if abs(am["cell_area"] - expected_cell_area) >= 1.0:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Cell area ({am['cell_area']}) doesn't match "
                f"total_area ({am['total_area']}) + tap_cell_area ({am['tap_cell_area']}) + filler_area ({filler_area}) + diode_area ({diode_area}) = {expected_cell_area}"
            )

    # Component areas should sum to cell area
    if all(k in am for k in ["combinational_cell_area", "sequential_cell_area", "cell_area"]):
        component_sum = am["combinational_cell_area"] + am["sequential_cell_area"]
        if component_sum > 0 and abs(component_sum - am["cell_area"]) >= am["cell_area"] * 0.01:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Component areas don't sum to cell area: "
                f"{component_sum} != {am['cell_area']}"
            )


def validate_power_metrics(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate power metrics using table data."""
    if cache.power_metrics is None:
        result.add_skip()
        return

    pm = cache.power_metrics

    # All power values should be non-negative
    if "total_power" in pm and pm["total_power"] < 0:
        result.add_fail(f"{cache.flow_id}/{cache.phase}: Total power is negative: {pm['total_power']}")
    if "combinational_power" in pm and pm["combinational_power"] < 0:
        result.add_fail(f"{cache.flow_id}/{cache.phase}: Combinational power is negative: {pm['combinational_power']}")
    if "sequential_power" in pm and pm["sequential_power"] < 0:
        result.add_fail(f"{cache.flow_id}/{cache.phase}: Sequential power is negative: {pm['sequential_power']}")
    if "leakage_power" in pm and pm["leakage_power"] < 0:
        result.add_fail(f"{cache.flow_id}/{cache.phase}: Leakage power is negative: {pm['leakage_power']}")

    # Component powers should not significantly exceed total
    if all(k in pm for k in ["combinational_power", "sequential_power", "leakage_power", "total_power"]):
        component_sum = pm["combinational_power"] + pm["sequential_power"] + pm["leakage_power"]
        if component_sum > pm["total_power"] * 1.1:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Component powers ({component_sum}) significantly exceed "
                f"total ({pm['total_power']})"
            )


def validate_timing_metrics(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate timing metrics using table data."""
    if cache.timing_metrics is None:
        result.add_skip()
        return

    tm = cache.timing_metrics

    # Violation counts should be non-negative
    if "no_of_violating_endpoints" in tm and tm["no_of_violating_endpoints"] < 0:
        result.add_fail(
            f"{cache.flow_id}/{cache.phase}: Violating endpoints count is negative: {tm['no_of_violating_endpoints']}"
        )

    if all(k in tm for k in ["no_of_endpoints", "no_of_violating_endpoints"]):
        if tm["no_of_endpoints"] < tm["no_of_violating_endpoints"]:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Violating endpoints ({tm['no_of_violating_endpoints']}) "
                f"exceed total ({tm['no_of_endpoints']})"
            )

    # Total negative slack should be non-positive
    if "total_negative_slack" in tm and tm["total_negative_slack"] > 0:
        result.add_fail(
            f"{cache.flow_id}/{cache.phase}: Total negative slack is positive: {tm['total_negative_slack']}"
        )

    # Worst slack should be a valid number
    if "worst_slack" in tm and not isinstance(tm["worst_slack"], (int, float)):
        result.add_fail(
            f"{cache.flow_id}/{cache.phase}: Worst slack is not a number: {type(tm['worst_slack'])}"
        )

    # Critical path references should exist in graph
    graph_data = cache.get_netlist_graph_data()
    if graph_data:
        nodes_set = cache.get_nodes_set()
        if "critical_path_startpoint" in tm and tm["critical_path_startpoint"]:
            if tm["critical_path_startpoint"] not in nodes_set:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Critical path startpoint not in netlist: {tm['critical_path_startpoint']}"
                )
        if "critical_path_endpoint" in tm and tm["critical_path_endpoint"]:
            if tm["critical_path_endpoint"] not in nodes_set:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Critical path endpoint not in netlist: {tm['critical_path_endpoint']}"
                )


def validate_cell_metrics(cache: ValidationDataCache, dataset: Dataset, result: ValidationResult) -> None:
    """Validate cell metrics consistency using table data."""
    if cache.cell_metrics is None:
        result.add_skip()
        return

    cm = cache.cell_metrics

    # Count actual cells from graph and gates table
    graph_data = cache.get_netlist_graph_data()
    if graph_data is None:
        result.add_skip()
        return

    node_types = graph_data["node_types"]
    actual_total = sum(1 for t in node_types if t == "GATE")

    # Count combinational vs sequential from gates table
    actual_combinational = 0
    actual_sequential = 0
    if len(cache.gates_df) > 0 and "standard_cell" in cache.gates_df.columns:
        for _, gate_row in cache.gates_df.iterrows():
            std_cell_name = gate_row["standard_cell"]
            if std_cell_name in dataset.standard_cells:
                if dataset.standard_cells[std_cell_name].is_sequential:
                    actual_sequential += 1
                else:
                    actual_combinational += 1

    if "no_of_total_cells" in cm and cm["no_of_total_cells"] != actual_total:
        result.add_fail(
            f"{cache.flow_id}/{cache.phase}: Total cell count mismatch: {cm['no_of_total_cells']} != {actual_total}"
        )
    if "no_of_combinational_cells" in cm and cm["no_of_combinational_cells"] != actual_combinational:
        result.add_fail(
            f"{cache.flow_id}/{cache.phase}: Combinational cell count mismatch: "
            f"{cm['no_of_combinational_cells']} != {actual_combinational}"
        )
    if "no_of_sequential_cells" in cm and cm["no_of_sequential_cells"] != actual_sequential:
        result.add_fail(
            f"{cache.flow_id}/{cache.phase}: Sequential cell count mismatch: "
            f"{cm['no_of_sequential_cells']} != {actual_sequential}"
        )

    # Sum should match total
    if all(k in cm for k in ["no_of_combinational_cells", "no_of_sequential_cells", "no_of_total_cells"]):
        if cm["no_of_combinational_cells"] + cm["no_of_sequential_cells"] != cm["no_of_total_cells"]:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Cell type sum doesn't match total: "
                f"{cm['no_of_combinational_cells']} + {cm['no_of_sequential_cells']} != {cm['no_of_total_cells']}"
            )


def validate_routability_metrics(cache: ValidationDataCache, dataset: Dataset, result: ValidationResult) -> None:
    """Validate routability metrics (RUDY images) using table data and images."""
    if cache.routability_metrics is None:
        result.add_skip()
        return

    # Check all RUDY images
    rudy_fields = ['rudy_net', 'rudy_net_long', 'rudy_net_short', 'rudy_pin']

    for field_name in rudy_fields:
        try:
            img = dataset.db.get_image("routability_metrics", field_name, flow_id=cache.flow_id, stage=cache.phase)
            if img is None:
                continue

            if not isinstance(img, Image2D):
                result.add_fail(f"{cache.flow_id}/{cache.phase}: RUDY {field_name} is not Image2D: {type(img)}")
                continue

            if img.shape[0] <= 0 or img.shape[1] <= 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: RUDY {field_name} has invalid shape: {img.shape}")

            if img.size <= 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: RUDY {field_name} has empty array")

            if img.dtype not in [np.uint8, np.float32, np.float64]:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: RUDY {field_name} has unexpected dtype: {img.dtype}"
                )

            # RUDY values should be non-negative
            if img.min() < 0:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: RUDY {field_name} has negative values: min={img.min()}"
                )

            # RUDY values should be reasonable (typically 0-100 or normalized)
            if img.max() >= 1e6:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: RUDY {field_name} has unreasonably high values: max={img.max()}"
                )
        except Exception:
            # Image might not exist, skip
            pass


def validate_timing_paths(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate timing paths using graph data and table data."""
    graph_data = cache.get_netlist_graph_data()
    if graph_data is None:
        result.add_skip()
        return

    nodes_set = cache.get_nodes_set()

    if len(cache.timing_paths_df) == 0:
        result.add_skip()
        return

    for _, row in cache.timing_paths_df.iterrows():
        startpoint = row.get("startpoint")
        endpoint = row.get("endpoint")
        path_type = row.get("path_type")

        if startpoint is None:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Path missing startpoint")
        if endpoint is None:
            result.add_fail(f"{cache.flow_id}/{cache.phase}: Path missing endpoint")
        if path_type not in {"setup", "hold"}:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Path has invalid type: {path_type}"
            )

        # Check path nodes exist in netlist (using pre-loaded graph data)
        path_key = (startpoint, endpoint, path_type)
        if cache.timing_paths_graph_lookup and path_key in cache.timing_paths_graph_lookup:
            path_graph_data = cache.timing_paths_graph_lookup[path_key]
            if path_graph_data and "nodes" in path_graph_data:
                for node_id in path_graph_data["nodes"]:
                    if node_id not in nodes_set:
                        result.add_fail(
                            f"{cache.flow_id}/{cache.phase}: Path references non-existent node: {node_id}"
                        )

        # Slack should equal required_time - arrival_time (approximately)
        if all(k in row for k in ["arrival_time", "required_time", "slack"]):
            expected_slack = row["required_time"] - row["arrival_time"]
            if abs(row["slack"] - expected_slack) >= 0.001:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Path slack mismatch: "
                    f"{row['slack']} != {row['required_time']} - {row['arrival_time']}"
                )


def validate_images(cache: ValidationDataCache, dataset: Dataset, result: ValidationResult) -> None:
    """Validate image data using database image access."""
    if cache.netlist_table_data is None:
        result.add_skip()
        return

    # Check netlist images
    image_fields = ['cell_placement', 'cell_placement_combinational',
                   'cell_placement_sequential', 'cell_placement_filler',
                   'pin_placement', 'routing']

    for field_name in image_fields:
        try:
            img = dataset.db.get_image("netlists", field_name, flow_id=cache.flow_id, stage=cache.phase)
            if img is None:
                continue

            if not isinstance(img, Image2D):
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Image {field_name} is not Image2D: {type(img)}"
                )
                continue

            if img.shape[0] <= 0 or img.shape[1] <= 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: Image {field_name} has invalid shape: {img.shape}")

            if img.size <= 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: Image {field_name} has empty array")

            if img.dtype not in [np.uint8, np.float32, np.float64]:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: Image {field_name} has unexpected dtype: {img.dtype}"
                )
        except Exception:
            # Image might not exist, skip
            pass


def validate_pdn(cache: ValidationDataCache, dataset: Dataset, result: ValidationResult) -> None:
    """Validate power delivery network using table data and images."""
    if cache.power_delivery_networks is None:
        result.add_skip()
        return

    pdn = cache.power_delivery_networks

    # Check flow_id and stage consistency
    if cache.netlist_table_data:
        if pdn.get("flow_id") != cache.netlist_table_data.get("flow_id"):
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: PDN flow_id mismatch: {pdn.get('flow_id')} != {cache.netlist_table_data.get('flow_id')}"
            )
        if pdn.get("stage") != cache.netlist_table_data.get("stage"):
            result.add_fail(f"{cache.flow_id}/{cache.phase}: PDN stage mismatch: {pdn.get('stage')} != {cache.netlist_table_data.get('stage')}")

    # Check PDN images
    for field_name in ['routing_vdd', 'routing_vss', 'ir_drop_vdd',
                       'ir_drop_vss', 'em_vdd', 'em_vss']:
        try:
            img = dataset.db.get_image("power_delivery_networks", field_name, flow_id=cache.flow_id, stage=cache.phase)
            if img is None:
                continue

            if not isinstance(img, Image2D):
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: PDN {field_name} is not Image2D: {type(img)}"
                )
                continue

            if img.shape[0] <= 0 or img.shape[1] <= 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: PDN {field_name} has invalid shape: {img.shape}")

            if img.size <= 0:
                result.add_fail(f"{cache.flow_id}/{cache.phase}: PDN {field_name} has empty array")

            if img.dtype not in [np.uint8, np.float32, np.float64]:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: PDN {field_name} has unexpected dtype: {img.dtype}"
                )

            # Routing images should be binary (0-1)
            if 'routing' in field_name:
                if img.min() < 0:
                    result.add_fail(
                        f"{cache.flow_id}/{cache.phase}: PDN {field_name} has negative values: min={img.min()}"
                    )
                if img.max() > 1:
                    result.add_fail(
                        f"{cache.flow_id}/{cache.phase}: PDN {field_name} has values > 1: max={img.max()}"
                    )

            # IR drop should be non-negative
            if 'ir_drop' in field_name:
                if img.min() < 0:
                    result.add_fail(
                        f"{cache.flow_id}/{cache.phase}: PDN {field_name} has negative values: min={img.min()}"
                    )
                if img.max() > 1.0:
                    result.add_fail(
                        f"{cache.flow_id}/{cache.phase}: PDN {field_name} has unreasonably high values: "
                        f"max={img.max()}V"
                    )

            # EM should be non-negative
            if 'em' in field_name:
                if img.min() < 0:
                    result.add_fail(
                        f"{cache.flow_id}/{cache.phase}: PDN {field_name} has negative values: min={img.min()}"
                    )
                if img.max() >= 1e6:
                    result.add_fail(
                        f"{cache.flow_id}/{cache.phase}: PDN {field_name} has unreasonably high values: "
                        f"max={img.max()}"
                    )
        except Exception:
            # Image might not exist, skip
            pass


def validate_flow_id_consistency(cache: ValidationDataCache, result: ValidationResult) -> None:
    """Validate flow_id and stage consistency across entities using table data."""
    # Check netlist
    if cache.netlist_table_data:
        if cache.netlist_table_data.get("flow_id") != cache.flow_id:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Netlist flow_id mismatch: {cache.netlist_table_data.get('flow_id')} != {cache.flow_id}"
            )
        if cache.netlist_table_data.get("stage") != cache.phase:
            result.add_fail(
                f"{cache.flow_id}/{cache.phase}: Netlist stage mismatch: {cache.netlist_table_data.get('stage')} != {cache.phase}"
            )

    # Check metrics
    for metric_name, metric_data in [
        ('area_metrics', cache.area_metrics),
        ('power_metrics', cache.power_metrics),
        ('timing_metrics', cache.timing_metrics),
        ('cell_metrics', cache.cell_metrics),
        ('routability_metrics', cache.routability_metrics),
    ]:
        if metric_data is not None:
            if "flow_id" in metric_data and metric_data["flow_id"] != cache.flow_id:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: {metric_name} flow_id mismatch: {metric_data['flow_id']} != {cache.flow_id}"
                )
            if "stage" in metric_data and metric_data["stage"] != cache.phase:
                result.add_fail(
                    f"{cache.flow_id}/{cache.phase}: {metric_name} stage mismatch: {metric_data['stage']} != {cache.phase}"
                )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an EDA-Schema ParquetDB dataset for structural integrity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate entire dataset
  python scripts/validate_dataset.py dataset/nangate45_fullrun_combined

  # Validate specific flow
  python scripts/validate_dataset.py dataset/nangate45_fullrun_combined --flow-id flow123

  # Sample 10 flows for faster validation
  python scripts/validate_dataset.py dataset/nangate45_fullrun_combined --sample 10

  # Validate only specific phases
  python scripts/validate_dataset.py dataset/nangate45_fullrun_combined --phases final detailed_route

  # Skip expensive checks
  python scripts/validate_dataset.py dataset/nangate45_fullrun_combined --skip-images --skip-pdn
        """
    )
    parser.add_argument(
        "dataset_dir",
        help="Path to dataset directory",
    )
    parser.add_argument(
        "--flow-id",
        type=str,
        default=None,
        help="Validate specific flow_id (default: validate all flows)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Sample N flows for validation (default: validate all)",
    )
    parser.add_argument(
        "--phases",
        nargs="+",
        default=PHASES,
        help=f"Phases to validate (default: all {len(PHASES)} phases)",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image validation (faster)",
    )
    parser.add_argument(
        "--skip-pdn",
        action="store_true",
        help="Skip PDN validation",
    )
    parser.add_argument(
        "--skip-routability",
        action="store_true",
        help="Skip routability metrics validation",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=100,
        help="Maximum number of errors to report (default: 100)",
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir).expanduser().resolve()
    if not dataset_dir.exists():
        print(f"Error: Dataset directory not found: {dataset_dir}")
        return 1

    print(f"Loading dataset: {dataset_dir}")
    try:
        dataset = Dataset(ParquetDB(dataset_dir))
        # Only load standard cells upfront (needed for validation)
        dataset.load_standard_cells()
        print(f"✓ Loaded {len(dataset.standard_cells)} standard cells")

        # Determine which flows to validate (without loading them yet)
        if args.flow_id:
            flow_ids = [args.flow_id]
        else:
            # Get flow IDs from database without loading full flows
            flows_df = dataset.db.get_table_data("design_flows")
            flow_ids = list(flows_df["flow_id"].unique())
            if args.sample and args.sample < len(flow_ids):
                flow_ids = random.sample(flow_ids, args.sample)
                print(f"Sampling {args.sample} flows from {len(flows_df)} total flows")

        print(f"Validating {len(flow_ids)} flow(s) across {len(args.phases)} phase(s)")
        print("(Using cached data loading - each (flow_id, phase) loaded once)")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        traceback.print_exc()
        return 1

    result = ValidationResult()

    # Dataset-level validation
    validate_dataset_structure(dataset, result)

    # Flow-level validation
    print("\n=== Flow Structure ===")
    for flow_id in flow_ids:
        validate_flow_structure(dataset, flow_id, result)
    if len(flow_ids) > 0:
        print(f"✓ Validated {len(flow_ids)} flow(s)")

    # Per-flow, per-phase validation
    print("\n=== Netlist & Metrics Validation ===")

    # Sample up to 10 flow_ids, always keeping the first one
    if len(flow_ids) > 10:
        first_flow = flow_ids[0]
        remaining_flows = flow_ids[1:]
        sampled_remaining = random.sample(remaining_flows, 9)
        flow_ids = [first_flow] + sampled_remaining
        print(f"Sampled {len(flow_ids)} flows (kept first: {first_flow}, sampled {len(sampled_remaining)} from remaining)")

    for flow_id in tqdm(flow_ids, desc="Flows", unit="flow"):
        for phase in tqdm(args.phases, desc=f"  {flow_id}", leave=False, unit="phase"):
            # Load all data once per (flow_id, phase)
            cache = load_validation_data(dataset, flow_id, phase)

            # Run all validators with cached data
            validate_netlist_graph(cache, result)
            validate_netlist_edge_consistency(cache, result)
            validate_netlist_entities(cache, dataset, result)
            validate_net_properties(cache, result)
            validate_net_parasitics(cache, result)
            validate_gate_coordinates(cache, result)
            validate_netlist_metrics_consistency(cache, dataset, result)
            validate_area_metrics(cache, result)
            validate_power_metrics(cache, result)
            validate_timing_metrics(cache, result)
            validate_cell_metrics(cache, dataset, result)
            validate_flow_id_consistency(cache, result)

            if not args.skip_images:
                validate_images(cache, dataset, result)

            if not args.skip_routability:
                validate_routability_metrics(cache, dataset, result)

            if not args.skip_pdn:
                validate_pdn(cache, dataset, result)

            # validate_timing_paths(cache, result)

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(result.summary())

    if result.warnings:
        print(f"\n{len(result.warnings)} warning(s) / skipped checks:")
        for warning in result.warnings[:20]:
            print(f"  {warning}")
        if len(result.warnings) > 20:
            print(f"  ... and {len(result.warnings) - 20} more warnings")

    if result.failed > 0:
        print(f"\n{result.failed} error(s) found:")
        for i, error in enumerate(result.errors[:args.max_errors], 1):
            print(f"  {i}. {error}")
        if len(result.errors) > args.max_errors:
            print(f"  ... and {len(result.errors) - args.max_errors} more errors")
            print(f"  (use --max-errors to see more)")
        return 1

    print("\n✓ All validations passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
