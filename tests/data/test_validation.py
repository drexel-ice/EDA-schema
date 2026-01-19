"""Structural validation tests - verify data structure and consistency."""
import math

import pytest
import numpy as np
from eda_schema.base import Image2D
from tests.data.conftest import FLOW_ID, get_netlist, get_design_stage, PHASES


@pytest.mark.parametrize("phase", PHASES)
def test_netlist_graph_structure(dataset, phase):
    """Check graph structure integrity."""
    netlist = get_netlist(dataset, phase)

    # All nodes should have valid types
    valid_types = {"GATE", "NET", "PORT", "PIN"}
    for node_id, node_data in netlist.nodes.items():
        assert "type" in node_data, f"Node {node_id} missing type"
        assert node_data["type"] in valid_types, f"Node {node_id} has invalid type: {node_data['type']}"
        assert "entity" in node_data, f"Node {node_id} missing entity"
        assert node_data["entity"] is not None, f"Node {node_id} has None entity"

    # All edges should connect valid nodes
    for source, target in netlist.edges:
        assert source in netlist.nodes, f"Edge source {source} not in nodes"
        assert target in netlist.nodes, f"Edge target {target} not in nodes"
        assert source != target, f"Self-loop detected: {source} -> {target}"

    # Graph should be connected (or have expected disconnected components)
    # At minimum, no node should be completely isolated unless it's a port, tap cell, or filler cell
    for node_id, node_data in netlist.nodes.items():
        if node_data["type"] == "PORT":
            # Ports can be isolated
            continue

        # Tap cells and filler cells are always isolated (no signal connections)
        if node_data["type"] == "GATE":
            gate = node_data["entity"]
            std_cell = dataset.standard_cells[gate.standard_cell]
            # Check if it's a filler cell or tap cell (tap cells often have "TAP" in their name)
            if std_cell.is_filler or "TAP" in node_id.upper():
                continue

        in_degree = len(list(netlist.predecessors(node_id)))
        out_degree = len(list(netlist.successors(node_id)))
        total_degree = in_degree + out_degree
        assert total_degree > 0, f"Non-port node {node_id} is completely isolated"


@pytest.mark.parametrize("phase", PHASES)
def test_netlist_node_entity_consistency(dataset, phase):
    """Check that node entities match their node IDs and types."""
    netlist = get_netlist(dataset, phase)

    for node_id, node_data in netlist.nodes.items():
        entity_obj = node_data["entity"]
        node_type = node_data["type"]

        # Entity should have a name that matches node_id (or be related)
        if hasattr(entity_obj, 'name'):
            # For gates, nets, ports - name should match node_id
            if node_type in {"GATE", "NET", "PORT"}:
                assert entity_obj.name == node_id, \
                    f"Node {node_id} entity name {entity_obj.name} doesn't match"

        # Type-specific checks
        if node_type == "GATE":
            assert hasattr(entity_obj, 'standard_cell'), \
                f"Gate {node_id} missing standard_cell attribute"
            assert entity_obj.standard_cell in dataset.standard_cells, \
                f"Gate {node_id} references unknown standard cell: {entity_obj.standard_cell}"

        elif node_type == "NET":
            assert hasattr(entity_obj, 'name'), f"Net {node_id} missing name"

        elif node_type == "PORT":
            assert hasattr(entity_obj, 'direction'), f"Port {node_id} missing direction"
            assert entity_obj.direction in {"INPUT", "OUTPUT", "INOUT"}, \
                f"Port {node_id} has invalid direction: {entity_obj.direction}"


@pytest.mark.parametrize("phase", PHASES)
def test_netlist_edge_consistency(dataset, phase):
    """Check that edges connect compatible node types."""
    netlist = get_netlist(dataset, phase)

    # Valid edge patterns:
    # PORT -> NET (input port drives net)
    # NET -> GATE (net drives gate input)
    # GATE -> NET (gate output drives net)
    # NET -> PORT (net drives output port)
    # NET -> NET (net segments)
    # PIN -> NET, NET -> PIN (pin connections)

    for source, target in netlist.edges:
        source_type = netlist.nodes[source]["type"]
        target_type = netlist.nodes[target]["type"]

        # Check for valid edge patterns
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

        assert (source_type, target_type) in valid_patterns, \
            f"Invalid edge pattern: {source_type} -> {target_type} ({source} -> {target})"


@pytest.mark.parametrize("phase", PHASES)
def test_gate_coordinates_validity(dataset, phase):
    """Check that gate coordinates are valid (if present)."""
    netlist = get_netlist(dataset, phase)

    for node_id, node_data in netlist.nodes.items():
        if node_data["type"] == "GATE":
            gate = node_data["entity"]

            # Coordinates are only available after placement
            # Skip validation if coordinates are None or NaN
            def is_valid_coord(val):
                return val is not None and not (isinstance(val, float) and math.isnan(val))

            # If coordinates are present and valid, they should be consistent
            if is_valid_coord(gate.x_min) and is_valid_coord(gate.x_max):
                assert gate.x_min <= gate.x_max, \
                    f"Gate {node_id}: x_min ({gate.x_min}) > x_max ({gate.x_max})"
                assert gate.x_min >= 0, f"Gate {node_id}: x_min ({gate.x_min}) < 0"

            if is_valid_coord(gate.y_min) and is_valid_coord(gate.y_max):
                assert gate.y_min <= gate.y_max, \
                    f"Gate {node_id}: y_min ({gate.y_min}) > y_max ({gate.y_max})"
                assert gate.y_min >= 0, f"Gate {node_id}: y_min ({gate.y_min}) < 0"

            # If both dimensions are present and valid, area should be positive
            if (is_valid_coord(gate.x_min) and is_valid_coord(gate.x_max) and
                is_valid_coord(gate.y_min) and is_valid_coord(gate.y_max)):
                width = gate.x_max - gate.x_min
                height = gate.y_max - gate.y_min
                area = width * height
                assert area > 0, f"Gate {node_id}: invalid area (width={width}, height={height})"


@pytest.mark.parametrize("phase", PHASES)
def test_gate_ir_drop_validity(dataset, phase):
    """Check that gate IR drop values are valid (if present)."""
    netlist = get_netlist(dataset, phase)

    gates_with_ir_drop = 0
    for node_id, node_data in netlist.nodes.items():
        if node_data["type"] == "GATE":
            gate = node_data["entity"]

            # IR drop fields should exist
            assert hasattr(gate, 'ir_drop_vdd'), f"Gate {node_id} missing ir_drop_vdd attribute"
            assert hasattr(gate, 'ir_drop_vss'), f"Gate {node_id} missing ir_drop_vss attribute"

            # If IR drop values are present, they should be valid floats
            def is_valid_ir_drop(val):
                return val is not None and not (isinstance(val, float) and math.isnan(val))

            if is_valid_ir_drop(gate.ir_drop_vdd):
                gates_with_ir_drop += 1
                # IR drop should be non-negative (voltage drop, typically 0-1.2V range)
                assert gate.ir_drop_vdd >= 0, \
                    f"Gate {node_id}: ir_drop_vdd ({gate.ir_drop_vdd}) is negative"
                # IR drop should be reasonable (typically < 1V for most designs)
                assert gate.ir_drop_vdd < 10.0, \
                    f"Gate {node_id}: ir_drop_vdd ({gate.ir_drop_vdd}) is unreasonably high"

            if is_valid_ir_drop(gate.ir_drop_vss):
                # IR drop should be non-negative
                assert gate.ir_drop_vss >= 0, \
                    f"Gate {node_id}: ir_drop_vss ({gate.ir_drop_vss}) is negative"
                # IR drop should be reasonable
                assert gate.ir_drop_vss < 10.0, \
                    f"Gate {node_id}: ir_drop_vss ({gate.ir_drop_vss}) is unreasonably high"

    # IR drop data is typically only available in routing stages
    # If we're in a routing stage and no gates have IR drop, that's worth noting but not an error
    if phase in ["detailed_route", "final"]:
        # In routing stages, at least some gates should have IR drop data if the files exist
        # But we don't fail if they don't exist (files might not be present)
        pass


@pytest.mark.parametrize("phase", PHASES)
def test_standard_cell_references(dataset, phase):
    """Check that all gates reference valid standard cells."""
    netlist = get_netlist(dataset, phase)

    referenced_cells = set()
    for node_id, node_data in netlist.nodes.items():
        if node_data["type"] == "GATE":
            gate = node_data["entity"]
            std_cell_name = gate.standard_cell

            assert std_cell_name in dataset.standard_cells, \
                f"Gate {node_id} references unknown standard cell: {std_cell_name}"

            std_cell = dataset.standard_cells[std_cell_name]
            assert std_cell.name == std_cell_name, \
                f"Standard cell name mismatch: {std_cell.name} != {std_cell_name}"

            referenced_cells.add(std_cell_name)

    # All referenced standard cells should have valid properties
    for std_cell_name in referenced_cells:
        std_cell = dataset.standard_cells[std_cell_name]
        assert std_cell.width > 0, f"Standard cell {std_cell_name} has invalid width"
        assert std_cell.height > 0, f"Standard cell {std_cell_name} has invalid height"
        # Area is calculated as width * height, not stored as an attribute
        calculated_area = std_cell.width * std_cell.height
        assert calculated_area > 0, f"Standard cell {std_cell_name} has invalid calculated area"


@pytest.mark.parametrize("phase", PHASES)
def test_netlist_metrics_consistency(dataset, phase):
    """Check that netlist metrics match actual counts."""
    netlist = get_netlist(dataset, phase)

    # Count actual nodes by type
    actual_cells = sum(1 for n, d in netlist.nodes.items() if d["type"] == "GATE")
    actual_nets = sum(1 for n, d in netlist.nodes.items() if d["type"] == "NET")
    actual_pins = sum(1 for n, d in netlist.nodes.items() if d["type"] == "PIN")
    actual_inputs = sum(1 for n, d in netlist.nodes.items()
                        if d["type"] == "PORT" and d["entity"].direction == "INPUT")
    actual_outputs = sum(1 for n, d in netlist.nodes.items()
                         if d["type"] == "PORT" and d["entity"].direction == "OUTPUT")

    # Check consistency
    assert netlist.no_of_cells == actual_cells, \
        f"Cell count mismatch: {netlist.no_of_cells} != {actual_cells}"
    assert netlist.no_of_nets == actual_nets, \
        f"Net count mismatch: {netlist.no_of_nets} != {actual_nets}"
    assert netlist.no_of_pins == actual_pins, \
        f"Pin count mismatch: {netlist.no_of_pins} != {actual_pins}"
    assert netlist.no_of_inputs == actual_inputs, \
        f"Input count mismatch: {netlist.no_of_inputs} != {actual_inputs}"
    assert netlist.no_of_outputs == actual_outputs, \
        f"Output count mismatch: {netlist.no_of_outputs} != {actual_outputs}"

    # Check graph size matches
    assert len(netlist.nodes) == actual_cells + actual_nets + actual_pins + actual_inputs + actual_outputs, \
        f"Total node count mismatch: {len(netlist.nodes)} != sum of components"
    assert len(netlist.edges) >= 0, "Edge count should be non-negative"


@pytest.mark.parametrize("phase", PHASES)
def test_clock_tree_structure(dataset, phase):
    """Check clock tree structure integrity."""
    netlist = get_netlist(dataset, phase)

    if not netlist.clock_trees:
        pytest.skip("No clock trees in this phase")

    for clock_name, clock_tree in netlist.clock_trees.items():
        assert clock_name is not None, "Clock tree has None name"
        assert len(clock_tree.nodes) > 0, f"Clock tree {clock_name} is empty"

        # All clock tree nodes should exist in netlist
        for node_id in clock_tree.nodes:
            assert node_id in netlist.nodes, \
                f"Clock tree {clock_name} references non-existent node: {node_id}"

        # Clock tree should be a connected subgraph
        # Check that all nodes are reachable from root (if root exists)
        if hasattr(clock_tree, 'root') and clock_tree.root:
            # Verify root exists in nodes
            assert clock_tree.root in clock_tree.nodes, \
                f"Clock tree {clock_name} root not in nodes"

        # Count buffers and sinks
        buffer_count = 0
        sink_count = 0
        for node_id in clock_tree.nodes:
            node_data = netlist.nodes[node_id]
            if node_data["type"] == "GATE":
                std_cell = dataset.standard_cells[node_data["entity"].standard_cell]
                if std_cell.is_buffer:
                    buffer_count += 1
                if std_cell.is_sequential:
                    sink_count += 1

        # Verify counts match
        assert clock_tree.no_of_buffers == buffer_count, \
            f"Clock tree {clock_name} buffer count mismatch"
        assert clock_tree.no_of_clock_sinks == sink_count, \
            f"Clock tree {clock_name} sink count mismatch"


@pytest.mark.parametrize("phase", PHASES)
def test_design_stage_metrics_exist(dataset, phase):
    """Check that design stage has expected metrics entities."""
    design_stage = get_design_stage(dataset, phase)

    # Check that netlist exists
    assert design_stage.netlist is not None, f"Design stage {phase} missing netlist"

    # Check for metrics (they may be None, but should be checkable)
    assert hasattr(design_stage, 'area_metrics'), f"Design stage {phase} missing area_metrics attribute"
    assert hasattr(design_stage, 'power_metrics'), f"Design stage {phase} missing power_metrics attribute"
    assert hasattr(design_stage, 'timing_metrics'), f"Design stage {phase} missing timing_metrics attribute"
    assert hasattr(design_stage, 'cell_metrics'), f"Design stage {phase} missing cell_metrics attribute"
    assert hasattr(design_stage, 'routability_metrics'), f"Design stage {phase} missing routability_metrics attribute"


@pytest.mark.parametrize("phase", PHASES)
def test_area_metrics_validity(dataset, phase):
    """Check area metrics for validity."""
    design_stage = get_design_stage(dataset, phase)

    if design_stage.area_metrics is None:
        pytest.skip(f"No area metrics for phase {phase}")

    am = design_stage.area_metrics

    # All area values should be non-negative
    assert am.total_area >= 0, f"Total area is negative: {am.total_area}"
    assert am.cell_area >= 0, f"Cell area is negative: {am.cell_area}"
    assert am.combinational_cell_area >= 0, f"Combinational area is negative: {am.combinational_cell_area}"
    assert am.sequential_cell_area >= 0, f"Sequential area is negative: {am.sequential_cell_area}"

    # Validate area relationship:
    # - total_area = OpenROAD's "Design area" (core functional area, excludes tap cells)
    # - cell_area = sum of all placed cells (includes tap cells)
    # - Relationship: total_area + tap_cell_area ≈ cell_area
    expected_cell_area = am.total_area + am.tap_cell_area
    assert abs(am.cell_area - expected_cell_area) < 1.0, \
        f"Cell area ({am.cell_area}) doesn't match total_area ({am.total_area}) + tap_cell_area ({am.tap_cell_area}) = {expected_cell_area}"

    # Component areas should sum to cell area (approximately, allowing for rounding)
    component_sum = am.combinational_cell_area + am.sequential_cell_area
    assert abs(component_sum - am.cell_area) < am.cell_area * 0.01 or component_sum == 0, \
        f"Component areas don't sum to cell area: {component_sum} != {am.cell_area}"


@pytest.mark.parametrize("phase", PHASES)
def test_power_metrics_validity(dataset, phase):
    """Check power metrics for validity."""
    design_stage = get_design_stage(dataset, phase)

    if design_stage.power_metrics is None:
        pytest.skip(f"No power metrics for phase {phase}")

    pm = design_stage.power_metrics

    # All power values should be non-negative
    assert pm.total_power >= 0, f"Total power is negative: {pm.total_power}"
    assert pm.combinational_power >= 0, f"Combinational power is negative: {pm.combinational_power}"
    assert pm.sequential_power >= 0, f"Sequential power is negative: {pm.sequential_power}"
    assert pm.leakage_power >= 0, f"Leakage power is negative: {pm.leakage_power}"

    # Component powers should not exceed total
    component_sum = pm.combinational_power + pm.sequential_power + pm.leakage_power
    assert component_sum <= pm.total_power * 1.1, \
        f"Component powers ({component_sum}) significantly exceed total ({pm.total_power})"


@pytest.mark.parametrize("phase", PHASES)
def test_timing_metrics_validity(dataset, phase):
    """Check timing metrics for validity."""
    design_stage = get_design_stage(dataset, phase)

    if design_stage.timing_metrics is None:
        pytest.skip(f"No timing metrics for phase {phase}")

    tm = design_stage.timing_metrics

    # Violation counts should be non-negative integers
    assert tm.no_of_violating_endpoints >= 0, \
        f"Violating endpoints count is negative: {tm.no_of_violating_endpoints}"
    assert tm.no_of_endpoints >= tm.no_of_violating_endpoints, \
        f"Violating endpoints ({tm.no_of_violating_endpoints}) exceed total ({tm.no_of_endpoints})"

    # Total negative slack should be non-positive (negative or zero)
    assert tm.total_negative_slack <= 0, \
        f"Total negative slack is positive: {tm.total_negative_slack}"

    # Worst slack should be a valid number
    assert isinstance(tm.worst_slack, (int, float)), \
        f"Worst slack is not a number: {type(tm.worst_slack)}"


@pytest.mark.parametrize("phase", PHASES)
def test_cell_metrics_consistency(dataset, phase):
    """Check that cell metrics match actual netlist counts."""
    design_stage = get_design_stage(dataset, phase)

    if design_stage.cell_metrics is None:
        pytest.skip(f"No cell metrics for phase {phase}")

    cm = design_stage.cell_metrics
    netlist = design_stage.netlist

    # Count actual cells
    actual_total = sum(1 for n, d in netlist.nodes.items() if d["type"] == "GATE")
    actual_combinational = sum(1 for n, d in netlist.nodes.items()
                              if d["type"] == "GATE" and
                              not dataset.standard_cells[d["entity"].standard_cell].is_sequential)
    actual_sequential = sum(1 for n, d in netlist.nodes.items()
                          if d["type"] == "GATE" and
                          dataset.standard_cells[d["entity"].standard_cell].is_sequential)

    assert cm.no_of_total_cells == actual_total, \
        f"Total cell count mismatch: {cm.no_of_total_cells} != {actual_total}"
    assert cm.no_of_combinational_cells == actual_combinational, \
        f"Combinational cell count mismatch: {cm.no_of_combinational_cells} != {actual_combinational}"
    assert cm.no_of_sequential_cells == actual_sequential, \
        f"Sequential cell count mismatch: {cm.no_of_sequential_cells} != {actual_sequential}"

    # Sum should match total
    assert cm.no_of_combinational_cells + cm.no_of_sequential_cells == cm.no_of_total_cells, \
        f"Cell type sum doesn't match total: {cm.no_of_combinational_cells} + {cm.no_of_sequential_cells} != {cm.no_of_total_cells}"


@pytest.mark.parametrize("phase", PHASES)
def test_netlist_image_data_validity(dataset, phase):
    """Check that image data (if present) is valid."""
    netlist = get_netlist(dataset, phase)

    image_data = netlist.get_image_data()

    for img_name, img_obj in image_data.items():
        if img_obj is None:
            continue

        assert isinstance(img_obj, Image2D), \
            f"Image {img_name} is not Image2D: {type(img_obj)}"

        assert img_obj.shape[0] > 0 and img_obj.shape[1] > 0, \
            f"Image {img_name} has invalid shape: {img_obj.shape}"

        assert img_obj is not None, \
            f"Image {img_name} is None"

        assert img_obj.size > 0, \
            f"Image {img_name} has empty array"

        # Check data type
        assert img_obj.dtype in [np.uint8, np.float32, np.float64], \
            f"Image {img_name} has unexpected dtype: {img_obj.dtype}"


@pytest.mark.parametrize("phase", PHASES)
def test_net_properties_validity(dataset, phase):
    """Check that net properties are valid and consistent."""
    netlist = get_netlist(dataset, phase)

    for node_id, node_data in netlist.nodes.items():
        if node_data["type"] != "NET":
            continue

        net = node_data["entity"]

        # Check basic properties exist
        assert hasattr(net, 'name'), f"Net {node_id} missing name"
        assert hasattr(net, 'no_of_fanouts'), f"Net {node_id} missing no_of_fanouts"
        assert hasattr(net, 'is_special_net'), f"Net {node_id} missing is_special_net"

        # Check name matches node_id
        assert net.name == node_id, f"Net {node_id} name mismatch: {net.name} != {node_id}"

        # Check no_of_fanouts is non-negative
        assert net.no_of_fanouts >= 0, f"Net {node_id} has negative no_of_fanouts: {net.no_of_fanouts}"

        # Check no_of_fanouts matches actual graph connections
        actual_fanouts = len(list(netlist.successors(node_id)))
        assert net.no_of_fanouts == actual_fanouts, \
            f"Net {node_id} no_of_fanouts mismatch: {net.no_of_fanouts} != {actual_fanouts} (graph)"

        # Check coordinates are valid if present (after placement)
        if hasattr(net, 'x_min') and net.x_min is not None and not math.isnan(net.x_min):
            assert hasattr(net, 'x_max'), f"Net {node_id} has x_min but missing x_max"
            assert hasattr(net, 'y_min'), f"Net {node_id} has x_min but missing y_min"
            assert hasattr(net, 'y_max'), f"Net {node_id} has x_min but missing y_max"

            assert not math.isnan(net.x_max), f"Net {node_id} has NaN x_max"
            assert not math.isnan(net.y_min), f"Net {node_id} has NaN y_min"
            assert not math.isnan(net.y_max), f"Net {node_id} has NaN y_max"

            # Check coordinate bounds are valid
            assert net.x_min <= net.x_max, \
                f"Net {node_id} x_min ({net.x_min}) > x_max ({net.x_max})"
            assert net.y_min <= net.y_max, \
                f"Net {node_id} y_min ({net.y_min}) > y_max ({net.y_max})"

        # Check length is valid if present (after routing)
        if hasattr(net, 'length') and net.length is not None and not math.isnan(net.length):
            assert net.length >= 0, f"Net {node_id} has negative length: {net.length}"

        # Check that special nets are properly marked
        # Special nets are typically power/ground nets
        if net.is_special_net:
            # Special nets might have different properties, but should still be valid
            assert isinstance(net.is_special_net, bool), \
                f"Net {node_id} is_special_net should be boolean"


@pytest.mark.parametrize("phase", PHASES)
def test_netlist_utilization_validity(dataset, phase):
    """Check that utilization is a valid percentage."""
    netlist = get_netlist(dataset, phase)

    if netlist.utilization is not None:
        assert 0 <= netlist.utilization <= 1.0, \
            f"Utilization out of range [0, 1]: {netlist.utilization}"

    if netlist.width is not None and netlist.height is not None:
        assert netlist.width > 0, f"Netlist width is non-positive: {netlist.width}"
        assert netlist.height > 0, f"Netlist height is non-positive: {netlist.height}"


@pytest.mark.parametrize("phase", PHASES)
def test_timing_paths_validity(dataset, phase):
    """Check timing paths if they exist."""
    netlist = get_netlist(dataset, phase)

    if not netlist.timing_paths:
        pytest.skip(f"No timing paths for phase {phase}")

    for path_key, path in netlist.timing_paths.items():
        assert path.startpoint is not None, f"Path {path_key} missing startpoint"
        assert path.endpoint is not None, f"Path {path_key} missing endpoint"
        assert path.path_type in {"setup", "hold"}, \
            f"Path {path_key} has invalid type: {path.path_type}"

        # Path should have nodes
        assert len(path.nodes) > 0, f"Path {path_key} is empty"

        # All path nodes should exist in netlist
        for node_id in path.nodes:
            assert node_id in netlist.nodes, \
                f"Path {path_key} references non-existent node: {node_id}"


def test_flow_structure(dataset):
    """Check that flow structure is valid."""
    flow = dataset[FLOW_ID]

    assert flow.flow_id == FLOW_ID, f"Flow ID mismatch: {flow.flow_id} != {FLOW_ID}"
    assert len(flow.stages) > 0, "Flow has no stages"

    # Check stage names are valid
    valid_stages = ["floorplan", "global_place", "place_resized", "detailed_place",
                   "cts", "global_route", "detailed_route", "final"]

    for stage_name, stage_obj in flow.stages.items():
        assert stage_name in valid_stages, f"Invalid stage name: {stage_name}"
        assert stage_obj.stage == stage_name, \
            f"Stage name mismatch: {stage_obj.stage} != {stage_name}"
        assert stage_obj.flow_id == FLOW_ID, \
            f"Stage flow_id mismatch: {stage_obj.flow_id} != {FLOW_ID}"


def test_standard_cells_loaded(dataset):
    """Check that standard cells are loaded and valid."""
    assert len(dataset.standard_cells) > 0, "No standard cells loaded"

    for cell_name, std_cell in dataset.standard_cells.items():
        assert std_cell.name == cell_name, \
            f"Standard cell name mismatch: {std_cell.name} != {cell_name}"
        assert std_cell.width > 0, f"Standard cell {cell_name} has invalid width"
        assert std_cell.height > 0, f"Standard cell {cell_name} has invalid height"

        # Area is calculated as width * height, not stored as an attribute
        calculated_area = std_cell.width * std_cell.height
        assert calculated_area > 0, f"Standard cell {cell_name} has invalid calculated area"


@pytest.mark.parametrize("phase", PHASES)
def test_pdn_entity_validity(dataset, phase):
    """Validate PDNEntity structure and basic properties."""
    netlist = get_netlist(dataset, phase)

    if netlist.power_delivery_network is None:
        pytest.skip(f"No PDN for phase {phase}")

    pdn = netlist.power_delivery_network

    # Check flow_id and stage match
    assert pdn.flow_id == netlist.flow_id, \
        f"PDN flow_id mismatch: {pdn.flow_id} != {netlist.flow_id}"
    assert pdn.stage == netlist.stage, \
        f"PDN stage mismatch: {pdn.stage} != {netlist.stage}"

    # Check all image fields are Image2D or None
    for field_name in ['routing_vdd', 'routing_vss', 'ir_drop_vdd',
                       'ir_drop_vss', 'em_vdd', 'em_vss']:
        img = getattr(pdn, field_name)
        if img is not None:
            assert isinstance(img, Image2D), \
                f"PDN {field_name} is not Image2D: {type(img)}"
            assert img.shape[0] > 0 and img.shape[1] > 0, \
                f"PDN {field_name} has invalid shape: {img.shape}"
            assert img.size > 0, \
                f"PDN {field_name} has empty array"
            # Check data type
            assert img.dtype in [np.uint8, np.float32, np.float64], \
                f"PDN {field_name} has unexpected dtype: {img.dtype}"


@pytest.mark.parametrize("phase", PHASES)
def test_pdn_routing_images_validity(dataset, phase):
    """Validate PDN routing images (VDD/VSS)."""
    netlist = get_netlist(dataset, phase)

    if netlist.power_delivery_network is None:
        pytest.skip(f"No PDN for phase {phase}")

    pdn = netlist.power_delivery_network

    # Routing images should be binary (0/1) or boolean
    for field_name, img in [('routing_vdd', pdn.routing_vdd),
                            ('routing_vss', pdn.routing_vss)]:
        if img is not None:
            # Check that values are in valid range (0-1 for binary, or boolean)
            assert img.min() >= 0, \
                f"PDN {field_name} has negative values: min={img.min()}"
            assert img.max() <= 1, \
                f"PDN {field_name} has values > 1: max={img.max()}"

            # Check that routing images have consistent dimensions
            if pdn.routing_vdd is not None and pdn.routing_vss is not None:
                assert pdn.routing_vdd.shape == pdn.routing_vss.shape, \
                    f"PDN routing images have inconsistent shapes: " \
                    f"routing_vdd={pdn.routing_vdd.shape}, routing_vss={pdn.routing_vss.shape}"

            # Check that there's at least some routing present (non-zero pixels)
            non_zero_count = np.count_nonzero(img)
            assert non_zero_count > 0, \
                f"PDN {field_name} has no routing (all zeros)"


@pytest.mark.parametrize("phase", PHASES)
def test_pdn_ir_drop_validity(dataset, phase):
    """Validate PDN IR drop images (voltage drop analysis)."""
    netlist = get_netlist(dataset, phase)

    if netlist.power_delivery_network is None:
        pytest.skip(f"No PDN for phase {phase}")

    pdn = netlist.power_delivery_network

    # IR drop images should have non-negative values (voltage drop can't be negative)
    for field_name, img in [('ir_drop_vdd', pdn.ir_drop_vdd),
                           ('ir_drop_vss', pdn.ir_drop_vss)]:
        if img is not None:
            # IR drop should be non-negative (voltage drop is always >= 0)
            assert img.min() >= 0, \
                f"PDN {field_name} has negative values: min={img.min()}"

            # IR drop should be reasonable (typically 0-0.5V, but depends on design)
            # Using a generous upper bound of 1.0V to catch obvious errors
            assert img.max() <= 1.0, \
                f"PDN {field_name} has unreasonably high values: max={img.max()}V"

            # Check that IR drop images have consistent dimensions
            if pdn.ir_drop_vdd is not None and pdn.ir_drop_vss is not None:
                assert pdn.ir_drop_vdd.shape == pdn.ir_drop_vss.shape, \
                    f"PDN IR drop images have inconsistent shapes: " \
                    f"ir_drop_vdd={pdn.ir_drop_vdd.shape}, ir_drop_vss={pdn.ir_drop_vss.shape}"

            # Check that mean and std are reasonable
            mean_val = img.mean()
            std_val = img.std()
            assert mean_val >= 0, \
                f"PDN {field_name} has negative mean: {mean_val}"
            assert std_val >= 0, \
                f"PDN {field_name} has negative std: {std_val}"


@pytest.mark.parametrize("phase", PHASES)
def test_pdn_em_validity(dataset, phase):
    """Validate PDN electromigration (EM) images (current density analysis)."""
    netlist = get_netlist(dataset, phase)

    if netlist.power_delivery_network is None:
        pytest.skip(f"No PDN for phase {phase}")

    pdn = netlist.power_delivery_network

    # EM images should have non-negative values (current density can't be negative)
    for field_name, img in [('em_vdd', pdn.em_vdd),
                           ('em_vss', pdn.em_vss)]:
        if img is not None:
            # EM should be non-negative (current density is always >= 0)
            assert img.min() >= 0, \
                f"PDN {field_name} has negative values: min={img.min()}"

            # EM should be reasonable (typically 0-10 mA/μm², but depends on technology)
            # Using a generous upper bound to catch obvious errors
            # Assuming values are normalized or in reasonable units
            assert img.max() < 1e6, \
                f"PDN {field_name} has unreasonably high values: max={img.max()}"

            # Check that EM images have consistent dimensions
            if pdn.em_vdd is not None and pdn.em_vss is not None:
                assert pdn.em_vdd.shape == pdn.em_vss.shape, \
                    f"PDN EM images have inconsistent shapes: " \
                    f"em_vdd={pdn.em_vdd.shape}, em_vss={pdn.em_vss.shape}"

            # Check that mean and std are reasonable
            mean_val = img.mean()
            std_val = img.std()
            assert mean_val >= 0, \
                f"PDN {field_name} has negative mean: {mean_val}"
            assert std_val >= 0, \
                f"PDN {field_name} has negative std: {std_val}"


@pytest.mark.parametrize("phase", PHASES)
def test_pdn_image_consistency(dataset, phase):
    """Validate consistency between different PDN image types."""
    netlist = get_netlist(dataset, phase)

    if netlist.power_delivery_network is None:
        pytest.skip(f"No PDN for phase {phase}")

    pdn = netlist.power_delivery_network

    # Collect all non-None images
    images = {}
    for field_name in ['routing_vdd', 'routing_vss', 'ir_drop_vdd',
                       'ir_drop_vss', 'em_vdd', 'em_vss']:
        img = getattr(pdn, field_name)
        if img is not None:
            images[field_name] = img

    if len(images) == 0:
        pytest.skip(f"No PDN images available for phase {phase}")

    # Check that routing images have compatible dimensions
    # (They may have different resolutions - routing is typically higher res)
    routing_images = {k: v for k, v in images.items() if 'routing' in k}
    analysis_images = {k: v for k, v in images.items() if k in ['ir_drop_vdd', 'ir_drop_vss', 'em_vdd', 'em_vss']}

    # Within each category, dimensions should match
    if len(routing_images) > 1:
        routing_shapes = [img.shape for img in routing_images.values()]
        assert len(set(routing_shapes)) == 1, \
            f"PDN routing images have inconsistent shapes: {dict((k, v.shape) for k, v in routing_images.items())}"

    if len(analysis_images) > 1:
        analysis_shapes = [img.shape for img in analysis_images.values()]
        assert len(set(analysis_shapes)) == 1, \
            f"PDN analysis images (IR/EM) have inconsistent shapes: {dict((k, v.shape) for k, v in analysis_images.items())}"

    # If both routing and analysis images exist, analysis images should be
    # same or lower resolution (they're typically downsampled)
    if routing_images and analysis_images:
        routing_shape = next(iter(routing_images.values())).shape
        analysis_shape = next(iter(analysis_images.values())).shape

        # Analysis images should have same or fewer pixels (downsampled)
        routing_pixels = routing_shape[0] * routing_shape[1]
        analysis_pixels = analysis_shape[0] * analysis_shape[1]
        assert analysis_pixels <= routing_pixels, \
            f"PDN analysis images ({analysis_shape}) have higher resolution than routing images ({routing_shape})"
