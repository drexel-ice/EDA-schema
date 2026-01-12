"""Data regression tests - track exact values to detect data changes."""
import math
import zlib

import pytest

from tests.data.conftest import FLOW_ID, get_netlist, get_design_stage


def is_nan_or_none(actual_value, expected_value):
    """
    Check if a coordinate value should be skipped (is NaN/None when expected to be).

    If expected_value is 0.0, it's treated as a placeholder for NaN/None (coordinates
    available only after placement). Returns True if we should skip the check.

    Args:
        actual_value: The actual value from the entity (may be NaN or None)
        expected_value: The expected value (0.0 means expect NaN/None)

    Returns:
        True if expected is 0.0 and actual is None/NaN (should skip check), False otherwise
    """
    return expected_value == 0.0 and (actual_value is None or math.isnan(actual_value))


@pytest.mark.parametrize(
    "phase, expected_values",
    [
        # Format: (phase, (no_of_cells, no_of_nets, no_of_inputs, no_of_outputs, no_of_buffer, no_of_inverter, no_of_sequential, width, height, utilization))
        ("floorplan", (312, 272, 36, 18, 0, 20, 41, 97.34, 97.34, 0.31)),
        ("global_place", (312, 272, 36, 18, 0, 20, 41, 97.34, 97.34, 0.31)),
        ("place_resized", (365, 325, 36, 18, 53, 20, 41, 97.34, 97.34, 0.35)),
        ("detailed_place", (365, 325, 36, 18, 53, 20, 41, 97.34, 97.34, 0.35)),
        ("cts", (439, 399, 36, 18, 61, 20, 41, 97.34, 97.34, 0.45)),
        ("global_route", (453, 413, 36, 18, 126, 20, 41, 97.34, 97.34, 0.46)),
        ("detailed_route", (1105, 413, 36, 18, 126, 20, 41, 97.34, 97.34, 0.98)),
        ("final", (1105, 413, 36, 18, 126, 20, 41, 97.34, 97.34, 0.98)),
    ]
)
def test_netlist_data(dataset, phase, expected_values):
    """Track netlist counts and dimensions per stage."""
    expected_no_of_cells, expected_no_of_nets, expected_no_of_inputs, expected_no_of_outputs, \
    expected_no_of_buffer, expected_no_of_inverter, expected_no_of_sequential, \
    expected_width, expected_height, expected_utilization = expected_values

    netlist = get_netlist(dataset, phase)

    # Check counts
    no_of_cells, no_of_nets, no_of_inputs, no_of_outputs = 0, 0, 0, 0
    no_of_buffer, no_of_inverter, no_of_sequential = 0, 0, 0

    for node, node_data in netlist.nodes.items():
        if node_data["type"] == "GATE":
            no_of_cells += 1
            std_cell = dataset.standard_cells[node_data["entity"].standard_cell]
            no_of_buffer += std_cell.is_buffer
            no_of_inverter += std_cell.is_inverter
            no_of_sequential += std_cell.is_sequential
        elif node_data["type"] == "NET":
            no_of_nets += 1
        elif node_data["type"] == "PORT":
            if node_data["entity"].direction == "INPUT":
                no_of_inputs += 1
            elif node_data["entity"].direction == "OUTPUT":
                no_of_outputs += 1

    assert netlist.no_of_inputs == no_of_inputs == expected_no_of_inputs
    assert netlist.no_of_outputs == no_of_outputs == expected_no_of_outputs
    assert netlist.no_of_cells == no_of_cells == expected_no_of_cells
    assert netlist.no_of_nets == no_of_nets == expected_no_of_nets

    assert no_of_buffer == expected_no_of_buffer
    assert no_of_inverter == expected_no_of_inverter
    assert no_of_sequential == expected_no_of_sequential

    # Check dimensions
    assert netlist.width == expected_width, \
            f"Netlist width changed: {netlist.width} != {expected_width}"
    assert netlist.height == expected_height, \
            f"Netlist height changed: {netlist.height} != {expected_height}"
    assert abs(netlist.utilization - expected_utilization) < 0.001, \
            f"Netlist utilization changed: {netlist.utilization} != {expected_utilization}"


@pytest.mark.parametrize(
    "phase, expected_no_of_buffers, expected_no_of_clock_sinks, expected_no_of_nets",
    [
        # Format: (phase, no_of_buffers, no_of_clock_sinks, no_of_nets)
        ("floorplan", 0, 35, 1),
        ("global_place", 0, 35, 1),
        ("place_resized", 0, 35, 1),
        ("detailed_place", 0, 35, 1),
        ("cts", 5, 35, 6),
        ("global_route", 5, 35, 6),
        ("detailed_route", 5, 35, 6),
        ("final", 5, 35, 6),
    ]
)
def test_clock_tree_sanity_check(dataset, phase, expected_no_of_buffers, expected_no_of_clock_sinks, expected_no_of_nets):
    """Track clock tree counts per stage."""
    netlist = get_netlist(dataset, phase)
    clock_tree = netlist.clock_trees["clk"]

    no_of_nets = sum(1 for node in clock_tree.nodes if netlist.nodes[node]["type"] == "NET")

    assert clock_tree.no_of_buffers == expected_no_of_buffers
    assert clock_tree.no_of_clock_sinks == expected_no_of_clock_sinks
    assert no_of_nets == expected_no_of_nets


@pytest.mark.parametrize(
    "phase, expected_values",
    [
        # Format: (phase, (total_area, cell_area, combinational_cell_area, sequential_cell_area, buffer_area, inverter_area))
        ("floorplan", (2247.0, 2371.024, 1630.314, 740.71, 0.0, 75.072)),
        ("global_place", (2247.0, 2371.024, 1630.314, 740.71, 0.0, 75.072)),
        ("place_resized", (2537.0, 2661.302, 1906.829, 754.474, 198.941, 75.072)),
        ("detailed_place", (2537.0, 2661.302, 1906.829, 754.474, 198.941, 75.072)),
        ("cts", (3292.0, 3415.776, 2656.298, 759.478, 287.776, 75.072)),
        ("global_route", (3351.0, 3474.582, 2721.36, 753.222, 759.478, 75.072)),
        ("detailed_route", (7207.0, 7330.781, 6577.558, 753.222, 759.478, 75.072)),
        ("final", (7207.0, 7330.781, 6577.558, 753.222, 759.478, 75.072)),
    ]
)
def test_area_metrics_data(dataset, phase, expected_values):
    """Track specific area metrics values."""
    design_stage = get_design_stage(dataset, phase)

    if design_stage.area_metrics is None:
        pytest.skip(f"No area metrics for phase {phase}")

    am = design_stage.area_metrics

    expected_total_area, expected_cell_area, expected_combinational_cell_area, \
    expected_sequential_cell_area, expected_buffer_area, expected_inverter_area = expected_values

    assert abs(am.total_area - expected_total_area) < 0.001, \
            f"Area metric total_area changed in {phase}: {am.total_area} != {expected_total_area}"
    assert abs(am.cell_area - expected_cell_area) < 0.001, \
            f"Area metric cell_area changed in {phase}: {am.cell_area} != {expected_cell_area}"
    assert abs(am.combinational_cell_area - expected_combinational_cell_area) < 0.001, \
            f"Area metric combinational_cell_area changed in {phase}: {am.combinational_cell_area} != {expected_combinational_cell_area}"
    assert abs(am.sequential_cell_area - expected_sequential_cell_area) < 0.001, \
            f"Area metric sequential_cell_area changed in {phase}: {am.sequential_cell_area} != {expected_sequential_cell_area}"
    assert abs(am.buffer_area - expected_buffer_area) < 0.001, \
            f"Area metric buffer_area changed in {phase}: {am.buffer_area} != {expected_buffer_area}"
    assert abs(am.inverter_area - expected_inverter_area) < 0.001, \
            f"Area metric inverter_area changed in {phase}: {am.inverter_area} != {expected_inverter_area}"


@pytest.mark.parametrize(
    "phase, expected_values",
    [
        # Format: (phase, (total_power, combinational_power, sequential_power, internal_power, switching_power, leakage_power))
        # Values are in μW (microwatts) - converted from Watts by multiplying by 1e6
        # Note: Database must be regenerated for these values to match (parser now converts W → μW)
        ("floorplan", (1100.0, 504.0, 591.0, 832.0, 263.0, 0.00101)),
        ("global_place", (1270.0, 656.0, 614.0, 861.0, 409.0, 0.00101)),
        ("place_resized", (1390.0, 773.0, 617.0, 909.0, 481.0, 0.00107)),
        ("detailed_place", (1390.0, 769.0, 621.0, 906.0, 484.0, 0.00107)),
        ("cts", (1800.0, 939.0, 624.0, 1170.0, 632.0, 0.00146)),
        ("global_route", (1840.0, 979.0, 625.0, 1190.0, 651.0, 0.00143)),
        ("detailed_route", (1840.0, 979.0, 625.0, 1190.0, 651.0, 0.00143)),
        ("final", (1840.0, 979.0, 625.0, 1190.0, 651.0, 0.00143)),
    ]
)
def test_power_metrics_data(dataset, phase, expected_values):
    """Track specific power metrics values."""
    design_stage = get_design_stage(dataset, phase)

    if design_stage.power_metrics is None:
        pytest.skip(f"No power metrics for phase {phase}")

    pm = design_stage.power_metrics

    expected_total_power, expected_combinational_power, expected_sequential_power, \
    expected_internal_power, expected_switching_power, expected_leakage_power = expected_values

    # Tolerance: 1e-3 for μW values (values are ~1e6 larger than before)
    assert abs(pm.total_power - expected_total_power) < 1e-3, \
            f"Power metric total_power changed in {phase}: {pm.total_power} != {expected_total_power}"
    assert abs(pm.combinational_power - expected_combinational_power) < 1e-3, \
            f"Power metric combinational_power changed in {phase}: {pm.combinational_power} != {expected_combinational_power}"
    assert abs(pm.sequential_power - expected_sequential_power) < 1e-3, \
            f"Power metric sequential_power changed in {phase}: {pm.sequential_power} != {expected_sequential_power}"
    assert abs(pm.internal_power - expected_internal_power) < 1e-3, \
            f"Power metric internal_power changed in {phase}: {pm.internal_power} != {expected_internal_power}"
    assert abs(pm.switching_power - expected_switching_power) < 1e-3, \
            f"Power metric switching_power changed in {phase}: {pm.switching_power} != {expected_switching_power}"
    assert abs(pm.leakage_power - expected_leakage_power) < 1e-3, \
            f"Power metric leakage_power changed in {phase}: {pm.leakage_power} != {expected_leakage_power}"


@pytest.mark.parametrize(
    "phase, expected_values",
    [
        # Format: (phase, (worst_slack, total_negative_slack, worst_arrival_time, worst_required_time, no_of_endpoints, no_of_violating_endpoints))
        ("floorplan", (-0.06515, -0.112382, 2.742, 2.677, 146, 3)),
        ("global_place", (-0.6051, -57.6401, 3.291, 2.686, 156, 156)),
        ("place_resized", (-0.4543, -16.46545, 3.14, 2.686, 134, 58)),
        ("detailed_place", (-0.475, -17.36155, 3.159, 2.684, 137, 66)),
        ("cts", (-0.3284, -25.55581, 3.014, 2.685, 142, 101)),
        ("global_route", (-0.2954, -14.357031, 2.98, 2.684, 138, 107)),
        ("detailed_route", (-0.2954, -14.357031, 2.98, 2.684, 138, 107)),
        ("final", (-0.2732, -12.472615, 2.959, 2.686, 137, 96)),
    ]
)
def test_timing_metrics_data(dataset, phase, expected_values):
    """Track specific timing metrics values."""
    design_stage = get_design_stage(dataset, phase)

    if design_stage.timing_metrics is None:
        pytest.skip(f"No timing metrics for phase {phase}")

    tm = design_stage.timing_metrics

    expected_worst_slack, expected_total_negative_slack, expected_worst_arrival_time, \
    expected_worst_required_time, expected_no_of_endpoints, expected_no_of_violating_endpoints = expected_values

    actual_value = getattr(tm, "worst_slack", None)
    if actual_value is not None:
        assert abs(actual_value - expected_worst_slack) < 1e-9, \
            f"Timing metric worst_slack changed in {phase}: {actual_value} != {expected_worst_slack}"

    actual_value = getattr(tm, "total_negative_slack", None)
    if actual_value is not None:
        assert abs(actual_value - expected_total_negative_slack) < 1e-9, \
            f"Timing metric total_negative_slack changed in {phase}: {actual_value} != {expected_total_negative_slack}"

    actual_value = getattr(tm, "worst_arrival_time", None)
    if actual_value is not None:
        assert abs(actual_value - expected_worst_arrival_time) < 1e-9, \
            f"Timing metric worst_arrival_time changed in {phase}: {actual_value} != {expected_worst_arrival_time}"

    actual_value = getattr(tm, "worst_required_time", None)
    if actual_value is not None:
        assert abs(actual_value - expected_worst_required_time) < 1e-9, \
            f"Timing metric worst_required_time changed in {phase}: {actual_value} != {expected_worst_required_time}"

    actual_value = getattr(tm, "no_of_endpoints", None)
    if actual_value is not None:
        assert actual_value == expected_no_of_endpoints, \
            f"Timing metric no_of_endpoints changed in {phase}: {actual_value} != {expected_no_of_endpoints}"

    actual_value = getattr(tm, "no_of_violating_endpoints", None)
    if actual_value is not None:
        assert actual_value == expected_no_of_violating_endpoints, \
            f"Timing metric no_of_violating_endpoints changed in {phase}: {actual_value} != {expected_no_of_violating_endpoints}"


@pytest.mark.parametrize(
    "phase, gate_name, expected_values",
    [
        # Format: (phase, gate_name, (standard_cell, x_min, y_min, x_max, y_max, no_of_inputs, no_of_outputs))
        ("floorplan", "TAP_TAPCELL_ROW_0_0", ("sky130_fd_sc_hd__tapvpwrvgnd_1", 0.0, 0.0, 0.0, 0.0, 0, 0)),
        ("global_place", "_192_", ("sky130_fd_sc_hd__xor2_1", 30.676, 74.928, 33.896, 77.648, 2, 1)),
        ("place_resized", "_192_", ("sky130_fd_sc_hd__xor2_1", 30.676, 74.928, 33.896, 77.648, 2, 1)),
        ("detailed_place", "_192_", ("sky130_fd_sc_hd__xor2_1", 29.9, 76.16, 33.12, 78.88, 2, 1)),
        ("cts", "_192_", ("sky130_fd_sc_hd__xor2_2", 27.14, 76.16, 33.12, 78.88, 2, 1)),
        ("global_route", "_192_", ("sky130_fd_sc_hd__xor2_2", 27.14, 76.16, 33.12, 78.88, 2, 1)),
        ("detailed_route", "FILLER_0_0_0", ("sky130_fd_sc_hd__fill_8", 5.06, 5.44, 8.74, 8.16, 0, 0)),
        ("final", "FILLER_0_0_0", ("sky130_fd_sc_hd__fill_8", 5.06, 5.44, 8.74, 8.16, 0, 0)),
    ]
)
def test_specific_gate_data(dataset, phase, gate_name, expected_values):
    """Track specific gate properties for regression testing."""
    netlist = get_netlist(dataset, phase)

    if gate_name not in netlist.nodes:
        pytest.skip(f"Gate {gate_name} not found in {phase}")

    node_data = netlist.nodes[gate_name]
    if node_data["type"] != "GATE":
        pytest.skip(f"Node {gate_name} is not a GATE in {phase}")

    gate = node_data["entity"]

    expected_standard_cell, expected_x_min, expected_y_min, expected_x_max, \
    expected_y_max, expected_no_of_inputs, expected_no_of_outputs = expected_values

    assert gate.standard_cell == expected_standard_cell, \
            f"Gate {gate_name} standard_cell changed in {phase}: {gate.standard_cell} != {expected_standard_cell}"

    # Handle NaN values for coordinates (coordinates available only after placement)
    if not is_nan_or_none(gate.x_min, expected_x_min):
        assert abs(gate.x_min - expected_x_min) < 0.001, \
                f"Gate {gate_name} x_min changed in {phase}: {gate.x_min} != {expected_x_min}"
    if not is_nan_or_none(gate.y_min, expected_y_min):
        assert abs(gate.y_min - expected_y_min) < 0.001, \
                f"Gate {gate_name} y_min changed in {phase}: {gate.y_min} != {expected_y_min}"
    if not is_nan_or_none(gate.x_max, expected_x_max):
        assert abs(gate.x_max - expected_x_max) < 0.001, \
                f"Gate {gate_name} x_max changed in {phase}: {gate.x_max} != {expected_x_max}"
    if not is_nan_or_none(gate.y_max, expected_y_max):
        assert abs(gate.y_max - expected_y_max) < 0.001, \
                f"Gate {gate_name} y_max changed in {phase}: {gate.y_max} != {expected_y_max}"

    assert gate.no_of_inputs == expected_no_of_inputs, \
            f"Gate {gate_name} no_of_inputs changed in {phase}: {gate.no_of_inputs} != {expected_no_of_inputs}"

    assert gate.no_of_outputs == expected_no_of_outputs, \
            f"Gate {gate_name} no_of_outputs changed in {phase}: {gate.no_of_outputs} != {expected_no_of_outputs}"


@pytest.mark.parametrize(
    "phase, net_name, expected_values",
    [
        # Format: (phase, net_name, (no_of_fanouts, length, x_min, y_min, x_max, y_max, is_special_net, hpwl, resistance, capacitance, total_coupling_capacitance))
        ("floorplan", "clk", (35, 0.0, 0.0, 0.0, 0.0, 0.0, False, 0.0, 0.0, 0.0, 0.0)),
        ("global_place", "clk", (35, 0.0, 0.0, 0.0, 0.0, 0.0, False, 148.584, 0.0, 0.0, 0.0)),
        ("place_resized", "clk", (35, 0.0, 0.0, 0.0, 0.0, 0.0, False, 148.584, 0.0, 0.0, 0.0)),
        ("detailed_place", "clk", (35, 0.0, 0.0, 0.0, 0.0, 0.0, False, 153.01, 0.0, 0.0, 0.0)),
        ("cts", "clk", (1, 0.0, 0.0, 0.0, 0.0, 0.0, False, 82.385, 0.0, 0.0, 0.0)),
        ("global_route", "clk", (1, 0.0, 0.0, 0.0, 0.0, 0.0, False, 82.385, 0.0, 0.0, 0.0)),
        ("detailed_route", "clk", (1, 81320.0, 0.46, 47.94, 47.61, 81.94, False, 0.0, 16.013900, 12.243500, 1.857135)),
        ("final", "clk", (1, 81320.0, 0.46, 47.94, 47.61, 81.94, False, 0.0, 16.013900, 12.243500, 1.857135)),
        ("floorplan", "_000_", (1, 0.0, 0.0, 0.0, 0.0, 0.0, False, 0.0, 0.0, 0.0, 0.0)),
        ("global_place", "_000_", (1, 0.0, 0.0, 0.0, 0.0, 0.0, False, 1.178, 0.0, 0.0, 0.0)),
        ("place_resized", "_000_", (1, 0.0, 0.0, 0.0, 0.0, 0.0, False, 1.466, 0.0, 0.0, 0.0)),
        ("detailed_place", "_000_", (1, 0.0, 0.0, 0.0, 0.0, 0.0, False, 4.07, 0.0, 0.0, 0.0)),
        ("cts", "_000_", (1, 0.0, 0.0, 0.0, 0.0, 0.0, False, 8.6, 0.0, 0.0, 0.0)),
        ("global_route", "_000_", (1, 0.0, 0.0, 0.0, 0.0, 0.0, False, 8.625, 0.0, 0.0, 0.0)),
        ("detailed_route", "_000_", (1, 7920.0, 54.97, 85.85, 61.87, 86.7, False, 0.0, 21.148850, 1.968980, 1.234204)),
        ("final", "_000_", (1, 7920.0, 54.97, 85.85, 61.87, 86.7, False, 0.0, 21.148850, 1.968980, 1.234204)),
        ("floorplan", "_038_", (2, 0.0, 0.0, 0.0, 0.0, 0.0, False, 0.0, 0.0, 0.0, 0.0)),
        ("global_place", "_038_", (2, 0.0, 0.0, 0.0, 0.0, 0.0, False, 16.998, 0.0, 0.0, 0.0)),
        ("place_resized", "_038_", (2, 0.0, 0.0, 0.0, 0.0, 0.0, False, 21.818, 0.0, 0.0, 0.0)),
        ("detailed_place", "_038_", (2, 0.0, 0.0, 0.0, 0.0, 0.0, False, 17.67, 0.0, 0.0, 0.0)),
        ("cts", "_038_", (2, 0.0, 0.0, 0.0, 0.0, 0.0, False, 17.67, 0.0, 0.0, 0.0)),
        ("global_route", "_038_", (2, 0.0, 0.0, 0.0, 0.0, 0.0, False, 17.67, 0.0, 0.0, 0.0)),
        ("detailed_route", "_038_", (2, 13300.0, 67.85, 34.51, 70.15, 45.05, False, 0.0, 29.544950, 1.676620, 0.529507)),
        ("final", "_038_", (2, 13300.0, 67.85, 34.51, 70.15, 45.05, False, 0.0, 29.544950, 1.676620, 0.529507)),
    ]
)
def test_specific_net_data(dataset, phase, net_name, expected_values):
    """Track specific net properties for regression testing."""
    netlist = get_netlist(dataset, phase)

    if net_name not in netlist.nodes:
        pytest.skip(f"Net {net_name} not found in {phase}")

    node_data = netlist.nodes[net_name]
    if node_data["type"] != "NET":
        pytest.skip(f"Node {net_name} is not a NET in {phase}")

    net = node_data["entity"]

    expected_no_of_fanouts, expected_length, expected_x_min, expected_y_min, \
    expected_x_max, expected_y_max, expected_is_special_net, expected_hpwl, \
    expected_resistance, expected_capacitance, expected_total_coupling_capacitance = expected_values

    assert net.no_of_fanouts == expected_no_of_fanouts, \
            f"Net {net_name} no_of_fanouts changed in {phase}: {net.no_of_fanouts} != {expected_no_of_fanouts}"

    # Handle NaN values for length and coordinates
    if not is_nan_or_none(net.length, expected_length):
        assert abs(net.length - expected_length) < 0.001, \
                f"Net {net_name} length changed in {phase}: {net.length} != {expected_length}"
    if not is_nan_or_none(net.x_min, expected_x_min):
        assert abs(net.x_min - expected_x_min) < 0.001, \
                f"Net {net_name} x_min changed in {phase}: {net.x_min} != {expected_x_min}"
    if not is_nan_or_none(net.y_min, expected_y_min):
        assert abs(net.y_min - expected_y_min) < 0.001, \
                f"Net {net_name} y_min changed in {phase}: {net.y_min} != {expected_y_min}"
    if not is_nan_or_none(net.x_max, expected_x_max):
        assert abs(net.x_max - expected_x_max) < 0.001, \
                f"Net {net_name} x_max changed in {phase}: {net.x_max} != {expected_x_max}"
    if not is_nan_or_none(net.y_max, expected_y_max):
        assert abs(net.y_max - expected_y_max) < 0.001, \
                f"Net {net_name} y_max changed in {phase}: {net.y_max} != {expected_y_max}"

    assert net.is_special_net == expected_is_special_net, \
            f"Net {net_name} is_special_net changed in {phase}: {net.is_special_net} != {expected_is_special_net}"

    # Handle NaN/None values for hpwl, resistance, capacitance, and coupling capacitance
    # Note: 0.0 in expected values means expect None/NaN (not yet available)
    if not is_nan_or_none(net.hpwl, expected_hpwl):
        assert abs(net.hpwl - expected_hpwl) < 0.001, \
                f"Net {net_name} hpwl changed in {phase}: {net.hpwl} != {expected_hpwl}"
    if not is_nan_or_none(net.resistance, expected_resistance):
        # Resistance is typically in Ohms, use appropriate tolerance
        tolerance = max(0.001, abs(expected_resistance) * 0.01) if expected_resistance != 0 else 0.001
        assert abs(net.resistance - expected_resistance) < tolerance, \
                f"Net {net_name} resistance changed in {phase}: {net.resistance} != {expected_resistance}"
    if not is_nan_or_none(net.capacitance, expected_capacitance):
        # Capacitance is typically in Farads, use appropriate tolerance
        tolerance = max(1e-18, abs(expected_capacitance) * 0.01) if expected_capacitance != 0 else 1e-18
        assert abs(net.capacitance - expected_capacitance) < tolerance, \
                f"Net {net_name} capacitance changed in {phase}: {net.capacitance} != {expected_capacitance}"
    if not is_nan_or_none(net.total_coupling_capacitance, expected_total_coupling_capacitance):
        # Coupling capacitance is typically in Farads, use appropriate tolerance
        tolerance = max(1e-18, abs(expected_total_coupling_capacitance) * 0.01) if expected_total_coupling_capacitance != 0 else 1e-18
        assert abs(net.total_coupling_capacitance - expected_total_coupling_capacitance) < tolerance, \
                f"Net {net_name} total_coupling_capacitance changed in {phase}: {net.total_coupling_capacitance} != {expected_total_coupling_capacitance}"


@pytest.mark.parametrize(
    "phase, port_name, expected_values",
    [
        # Format: (phase, port_name, (direction, x, y))
        ("floorplan", "clk_input", ("INPUT", 0.4, 88.74)),
        ("floorplan", "req_msg_0__input", ("INPUT", 90.39, 0.242)),
        ("global_place", "clk_input", ("INPUT", 0.4, 81.94)),
        ("global_place", "req_msg_0__input", ("INPUT", 0.4, 16.66)),
        ("place_resized", "clk_input", ("INPUT", 0.4, 81.94)),
        ("place_resized", "req_msg_0__input", ("INPUT", 0.4, 16.66)),
        ("detailed_place", "clk_input", ("INPUT", 0.4, 81.94)),
        ("detailed_place", "req_msg_0__input", ("INPUT", 0.4, 16.66)),
        ("cts", "clk_input", ("INPUT", 0.4, 81.94)),
        ("cts", "req_msg_0__input", ("INPUT", 0.4, 16.66)),
        ("global_route", "clk_input", ("INPUT", 0.4, 81.94)),
        ("global_route", "req_msg_0__input", ("INPUT", 0.4, 16.66)),
        ("detailed_route", "clk_input", ("INPUT", 0.4, 81.94)),
        ("detailed_route", "req_msg_0__input", ("INPUT", 0.4, 16.66)),
        ("final", "clk_input", ("INPUT", 0.4, 81.94)),
        ("final", "req_msg_0__input", ("INPUT", 0.4, 16.66)),
    ]
)
def test_specific_port_data(dataset, phase, port_name, expected_values):
    """Track specific port properties for regression testing."""
    netlist = get_netlist(dataset, phase)

    if port_name not in netlist.nodes:
        pytest.skip(f"Port {port_name} not found in {phase}")

    node_data = netlist.nodes[port_name]
    if node_data["type"] != "PORT":
        pytest.skip(f"Node {port_name} is not a PORT in {phase}")

    port = node_data["entity"]

    expected_direction, expected_x, expected_y = expected_values

    assert port.direction == expected_direction, \
            f"Port {port_name} direction changed in {phase}: {port.direction} != {expected_direction}"

    assert abs(port.x - expected_x) < 0.001, \
            f"Port {port_name} x changed in {phase}: {port.x} != {expected_x}"

    assert abs(port.y - expected_y) < 0.001, \
            f"Port {port_name} y changed in {phase}: {port.y} != {expected_y}"


@pytest.mark.parametrize(
    "phase, expected_values",
    [
        # Format: (phase, (no_of_buffers, no_of_clock_sinks, no_of_nets))
        ("floorplan", (0, 35, 1)),
        ("global_place", (0, 35, 1)),
        ("place_resized", (0, 35, 1)),
        ("detailed_place", (0, 35, 1)),
        ("cts", (5, 35, 6)),
        ("global_route", (5, 35, 6)),
        ("detailed_route", (5, 35, 6)),
        ("final", (5, 35, 6)),
    ]
)
def test_clock_tree_data(dataset, phase, expected_values):
    """Track specific clock tree properties."""
    netlist = get_netlist(dataset, phase)

    if not netlist.clock_trees:
        pytest.skip(f"No clock trees for phase {phase}")

    expected_no_of_buffers, expected_no_of_clock_sinks, expected_no_of_nets = expected_values

    # Check the "clk" clock tree
    clock_name = "clk"
    if clock_name not in netlist.clock_trees:
        pytest.skip(f"No clock tree '{clock_name}' for phase {phase}")

    clock_tree = netlist.clock_trees[clock_name]

    assert clock_tree.no_of_buffers == expected_no_of_buffers, \
            f"Clock tree {clock_name} no_of_buffers changed in {phase}: {clock_tree.no_of_buffers} != {expected_no_of_buffers}"

    assert clock_tree.no_of_clock_sinks == expected_no_of_clock_sinks, \
            f"Clock tree {clock_name} no_of_clock_sinks changed in {phase}: {clock_tree.no_of_clock_sinks} != {expected_no_of_clock_sinks}"

    # Count nets in clock tree
    actual_no_of_nets = sum(1 for node in clock_tree.nodes
                           if netlist.nodes[node]["type"] == "NET")
    assert actual_no_of_nets == expected_no_of_nets, \
        f"Clock tree {clock_name} no_of_nets changed in {phase}: {actual_no_of_nets} != {expected_no_of_nets}"


@pytest.mark.parametrize(
    "phase, image_name, expected_shape, expected_checksum",
    [
        # Format: (phase, image_name, (height, width), checksum)
        ("global_place", "cell_placement", (695, 695), 0x5ed6df02),
        ("global_place", "cell_placement_combinational", (695, 695), 0x9ac02102),
        ("global_place", "cell_placement_sequential", (695, 695), 0xf1066597),
        ("global_place", "pin_placement", (695, 695), 0x032546b1),
        ("place_resized", "cell_placement", (695, 695), 0x541cbe1e),
        ("place_resized", "cell_placement_combinational", (695, 695), 0x99501267),
        ("place_resized", "cell_placement_sequential", (695, 695), 0x1fc3e312),
        ("place_resized", "pin_placement", (695, 695), 0x41ea9e79),
        ("detailed_place", "cell_placement", (695, 695), 0x22030b0e),
        ("detailed_place", "cell_placement_combinational", (695, 695), 0xa395601f),
        ("detailed_place", "cell_placement_sequential", (695, 695), 0x35fbc11d),
        ("detailed_place", "pin_placement", (695, 695), 0xc6e87d67),
        ("cts", "cell_placement", (695, 695), 0x0482a71b),
        ("cts", "cell_placement_combinational", (695, 695), 0x968df5bf),
        ("cts", "cell_placement_sequential", (695, 695), 0x88af445b),
        ("cts", "pin_placement", (695, 695), 0xa9536975),
        ("global_route", "cell_placement", (695, 695), 0xb75b5b27),
        ("global_route", "cell_placement_combinational", (695, 695), 0xf3c58e31),
        ("global_route", "cell_placement_sequential", (695, 695), 0x32f71952),
        ("global_route", "pin_placement", (695, 695), 0xf969c1a4),
        ("detailed_route", "cell_placement", (695, 695), 0xb28ae2a1),
        ("detailed_route", "routing", (695, 695), 0x8f7e2894),
        ("detailed_route", "cell_placement_combinational", (695, 695), 0xf3c58e31),
        ("detailed_route", "cell_placement_sequential", (695, 695), 0x32f71952),
        ("detailed_route", "pin_placement", (695, 695), 0xf969c1a4),
        ("final", "cell_placement", (695, 695), 0xb28ae2a1),
        ("final", "routing", (695, 695), 0x8f7e2894),
        ("final", "cell_placement_combinational", (695, 695), 0xf3c58e31),
        ("final", "cell_placement_sequential", (695, 695), 0x32f71952),
        ("final", "cell_placement_filler", (695, 695), 0xba27e97f),
        ("final", "pin_placement", (695, 695), 0xf969c1a4),
    ]
)
def test_image_shapes_data(dataset, phase, image_name, expected_shape, expected_checksum):
    """Track image shapes and checksums for regression testing."""
    netlist = get_netlist(dataset, phase)

    image_data = netlist.get_image_data()

    if image_name not in image_data or image_data[image_name] is None:
        pytest.skip(f"Image {image_name} not found in {phase}")

    img = image_data[image_name]
    actual_shape = img.shape
    expected_height, expected_width = expected_shape

    assert actual_shape == (expected_height, expected_width), \
        f"Image {image_name} shape changed in {phase}: {actual_shape} != {(expected_height, expected_width)}"

    actual_checksum = zlib.crc32(img.tobytes())
    assert actual_checksum == expected_checksum, \
        f"Image {image_name} checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_checksum:08x}"


@pytest.mark.parametrize(
    "phase, rudy_metric_name, expected_shape, expected_checksum",
    [
        # Format: (phase, rudy_metric_name, (height, width), checksum)
        # RUDY metrics are only available after detailed routing
        ("detailed_route", "rudy_net", (14, 14), 0xf3b831b9),
        ("detailed_route", "rudy_net_long", (14, 14), 0xf3b831b9),
        ("detailed_route", "rudy_net_short", (14, 14), 0x1966e863),
        ("detailed_route", "rudy_pin", (14, 14), 0x9edd34ff),
        ("detailed_route", "rudy_pin_long", (14, 14), 0x9edd34ff),
        ("final", "rudy_net", (14, 14), 0xf3b831b9),
        ("final", "rudy_net_long", (14, 14), 0xf3b831b9),
        ("final", "rudy_net_short", (14, 14), 0x1966e863),
        ("final", "rudy_pin", (14, 14), 0x9edd34ff),
        ("final", "rudy_pin_long", (14, 14), 0x9edd34ff),
    ]
)
def test_routability_metrics_data(dataset, phase, rudy_metric_name, expected_shape, expected_checksum):
    """Track routability metrics image shapes and checksums."""
    design_stage = get_design_stage(dataset, phase)

    if design_stage.routability_metrics is None:
        pytest.skip(f"No routability metrics for phase {phase}")

    rm = design_stage.routability_metrics
    rudy_image = getattr(rm, rudy_metric_name, None)

    if rudy_image is None:
        pytest.skip(f"RUDY metric {rudy_metric_name} not available in {phase}")

    actual_shape = rudy_image.shape
    expected_height, expected_width = expected_shape

    assert actual_shape == (expected_height, expected_width), \
        f"RUDY {rudy_metric_name} shape changed in {phase}: {actual_shape} != {(expected_height, expected_width)}"

    actual_checksum = zlib.crc32(rudy_image.tobytes())
    assert actual_checksum == expected_checksum, \
        f"RUDY {rudy_metric_name} checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_checksum:08x}"


@pytest.mark.parametrize(
    "phase, expected_no_of_paths",
    [
        ("floorplan", 299),
        ("global_place", 309),
        ("place_resized", 283),
        ("detailed_place", 288),
        ("cts", 298),
        ("global_route", 288),
        ("detailed_route", 288),
        ("final", 287),
    ]
)
def test_timing_path_count(dataset, phase, expected_no_of_paths):
    """Track number of timing paths per stage."""
    netlist = get_netlist(dataset, phase)

    # Load timing paths if not already loaded
    if not netlist.timing_paths:
        timing_paths = dataset.load_timing_paths(flow_id=FLOW_ID, stage=phase, netlist_entity=netlist)
        netlist.timing_paths = timing_paths

    if not netlist.timing_paths:
        pytest.skip(f"No timing paths for phase {phase}")

    actual_count = len(netlist.timing_paths)

    assert actual_count == expected_no_of_paths, \
            f"Number of timing paths changed in {phase}: {actual_count} != {expected_no_of_paths}"


@pytest.mark.parametrize(
    "phase, expected_values",
    [
        # Format: (phase, (min_slack, max_slack, min_arrival, max_arrival, min_required, max_required))
        ("floorplan", (-0.1179, 0.5473, 0.0384, 2.742, 0.1563, 2.8)),
        ("global_place", (-0.6051, 0.5265, 0.04076, 3.291, 0.1552, 2.739)),
        ("place_resized", (-0.4543, 0.5882, 0.1867, 3.14, 0.1577, 2.8)),
        ("detailed_place", (-0.475, 0.5971, 0.1937, 3.159, 0.1566, 2.8)),
        ("cts", (-0.3284, 0.6149, 0.448, 3.016, 0.1555, 2.8)),
        ("global_route", (-0.2954, 0.6261, 0.4212, 2.98, 0.1554, 2.8)),
        ("detailed_route", (-0.2954, 0.6261, 0.4212, 2.98, 0.1554, 2.8)),
        ("final", (-0.2732, 0.6147, 0.4159, 2.959, 0.1566, 2.8)),
    ]
)
def test_timing_path_min_max(dataset, phase, expected_values):
    """Track min/max timing path values (slack, arrival_time, required_time)."""
    netlist = get_netlist(dataset, phase)

    # Load timing paths if not already loaded
    if not netlist.timing_paths:
        timing_paths = dataset.load_timing_paths(flow_id=FLOW_ID, stage=phase, netlist_entity=netlist)
        netlist.timing_paths = timing_paths

    if not netlist.timing_paths:
        pytest.skip(f"No timing paths for phase {phase}")

    expected_min_slack, expected_max_slack, expected_min_arrival, \
    expected_max_arrival, expected_min_required, expected_max_required = expected_values

    slacks = [path.slack for path in netlist.timing_paths.values()]
    arrival_times = [path.arrival_time for path in netlist.timing_paths.values()]
    required_times = [path.required_time for path in netlist.timing_paths.values()]

    assert min(slacks) == expected_min_slack, \
            f"Min slack changed in {phase}: {min(slacks)} != {expected_min_slack}"
    assert max(slacks) == expected_max_slack, \
            f"Max slack changed in {phase}: {max(slacks)} != {expected_max_slack}"
    assert abs(min(arrival_times) - expected_min_arrival) < 1e-9, \
            f"Min arrival_time changed in {phase}: {min(arrival_times)} != {expected_min_arrival}"
    assert abs(max(arrival_times) - expected_max_arrival) < 1e-9, \
            f"Max arrival_time changed in {phase}: {max(arrival_times)} != {expected_max_arrival}"
    assert abs(min(required_times) - expected_min_required) < 1e-9, \
            f"Min required_time changed in {phase}: {min(required_times)} != {expected_min_required}"
    assert abs(max(required_times) - expected_max_required) < 1e-9, \
            f"Max required_time changed in {phase}: {max(required_times)} != {expected_max_required}"


@pytest.mark.parametrize(
    "phase, expected_values",
    [
        # Format: (phase, (critical_slack, critical_arrival, critical_required, critical_no_of_pins))
        ("floorplan", (-0.06515, 2.742, 2.677, 26)),
        ("global_place", (-0.6051, 3.291, 2.686, 22)),
        ("place_resized", (-0.4543, 3.14, 2.686, 20)),
        ("detailed_place", (-0.475, 3.159, 2.684, 20)),
        ("cts", (-0.3284, 3.014, 2.685, 30)),
        ("global_route", (-0.2954, 2.98, 2.684, 30)),
        ("detailed_route", (-0.2954, 2.98, 2.684, 30)),
        ("final", (-0.2732, 2.959, 2.686, 28)),
    ]
)
def test_critical_timing_path_data(dataset, phase, expected_values):
    """Track critical timing path values."""
    netlist = get_netlist(dataset, phase)

    # Load timing paths if not already loaded
    if not netlist.timing_paths:
        timing_paths = dataset.load_timing_paths(flow_id=FLOW_ID, stage=phase, netlist_entity=netlist)
        netlist.timing_paths = timing_paths

    if not netlist.timing_paths:
        pytest.skip(f"No timing paths for phase {phase}")

    critical_paths = [path for path in netlist.timing_paths.values() if path.is_critical_path]

    if not critical_paths:
        pytest.skip(f"No critical timing paths for phase {phase}")

    expected_critical_slack, expected_critical_arrival, expected_critical_required, expected_critical_no_of_pins = expected_values

    # Get worst critical path (most negative slack)
    worst_critical = min(critical_paths, key=lambda p: p.slack)

    assert abs(worst_critical.slack - expected_critical_slack) < 1e-9, \
            f"Critical path slack changed in {phase}: {worst_critical.slack} != {expected_critical_slack}"
    assert abs(worst_critical.arrival_time - expected_critical_arrival) < 1e-9, \
            f"Critical path arrival_time changed in {phase}: {worst_critical.arrival_time} != {expected_critical_arrival}"
    assert abs(worst_critical.required_time - expected_critical_required) < 1e-9, \
            f"Critical path required_time changed in {phase}: {worst_critical.required_time} != {expected_critical_required}"
    assert worst_critical.no_of_pins == expected_critical_no_of_pins, \
            f"Critical path no_of_pins changed in {phase}: {worst_critical.no_of_pins} != {expected_critical_no_of_pins}"


@pytest.mark.parametrize(
    "phase, startpoint, endpoint, path_type, expected_values",
    [
        # Format: (phase, startpoint, endpoint, path_type, (slack, arrival_time, required_time, no_of_pins, is_critical_path))
        ("floorplan", "reset", "_380_/D", "hold", (-0.1179, 0.0384, 0.1563, 2, False)),
        ("floorplan", "reset", "_379_/D", "hold", (-0.1176, 0.03975, 0.1574, 2, False)),
        ("global_place", "reset", "_379_/D", "hold", (-0.1154, 0.04124, 0.1567, 2, False)),
        ("global_place", "reset", "_380_/D", "hold", (-0.1144, 0.04076, 0.1552, 2, False)),
        ("place_resized", "req_msg_3_", "_384_/D", "hold", (0.02374, 0.1984, 0.1747, 4, False)),
        ("place_resized", "resp_rdy", "_378_/D", "hold", (0.0244, 0.1999, 0.1755, 6, False)),
        ("detailed_place", "req_msg_14_", "_395_/D", "hold", (0.01973, 0.1937, 0.174, 4, False)),
        ("detailed_place", "resp_rdy", "_378_/D", "hold", (0.02027, 0.1955, 0.1752, 6, False)),
        ("cts", "_379_/Q", "_379_/D", "hold", (0.281, 0.448, 0.1669, 10, False)),
        ("cts", "_410_/Q", "_410_/D", "hold", (0.3029, 0.4726, 0.1696, 10, False)),
        ("global_route", "req_msg_20_", "_401_/D", "hold", (0.2536, 0.4212, 0.1676, 8, False)),
        ("global_route", "req_msg_31_", "_412_/D", "hold", (0.2553, 0.4227, 0.1674, 8, False)),
        ("detailed_route", "req_msg_20_", "_401_/D", "hold", (0.2536, 0.4212, 0.1676, 8, False)),
        ("detailed_route", "req_msg_31_", "_412_/D", "hold", (0.2553, 0.4227, 0.1674, 8, False)),
        ("final", "req_msg_20_", "_401_/D", "hold", (0.2482, 0.4159, 0.1677, 8, False)),
        ("final", "req_msg_31_", "_412_/D", "hold", (0.2531, 0.4198, 0.1667, 8, False)),
        ("floorplan", "_381_/Q", "_412_/D", "setup", (-0.06515, 2.742, 2.677, 26, True)),
        ("global_place", "_397_/Q", "_391_/D", "setup", (-0.6051, 3.291, 2.686, 22, True)),
        ("place_resized", "_381_/Q", "_385_/D", "setup", (-0.4543, 3.14, 2.686, 20, True)),
        ("detailed_place", "_381_/Q", "_389_/D", "setup", (-0.475, 3.159, 2.684, 20, True)),
        ("cts", "_397_/Q", "_387_/D", "setup", (-0.3284, 3.014, 2.685, 30, True)),
        ("global_route", "_397_/Q", "_395_/D", "setup", (-0.2954, 2.98, 2.684, 30, True)),
        ("detailed_route", "_397_/Q", "_395_/D", "setup", (-0.2954, 2.98, 2.684, 30, True)),
        ("final", "_381_/Q", "_395_/D", "setup", (-0.2732, 2.959, 2.686, 28, True)),
    ]
)
def test_timing_path_sample_data(dataset, phase, startpoint, endpoint, path_type, expected_values):
    """Track specific timing path properties for sample paths."""
    netlist = get_netlist(dataset, phase)

    # Load timing paths if not already loaded
    if not netlist.timing_paths:
        timing_paths = dataset.load_timing_paths(flow_id=FLOW_ID, stage=phase, netlist_entity=netlist)
        netlist.timing_paths = timing_paths

    if not netlist.timing_paths:
        pytest.skip(f"No timing paths for phase {phase}")

    path_key = (startpoint, endpoint, path_type)
    if path_key not in netlist.timing_paths:
        pytest.skip(f"Timing path {path_key} not found in {phase}")

    path = netlist.timing_paths[path_key]
    expected_slack, expected_arrival, expected_required, expected_no_of_pins, expected_is_critical = expected_values

    assert abs(path.slack - expected_slack) < 1e-9, \
            f"Timing path {path_key} slack changed in {phase}: {path.slack} != {expected_slack}"

    assert abs(path.arrival_time - expected_arrival) < 1e-9, \
            f"Timing path {path_key} arrival_time changed in {phase}: {path.arrival_time} != {expected_arrival}"

    assert abs(path.required_time - expected_required) < 1e-9, \
            f"Timing path {path_key} required_time changed in {phase}: {path.required_time} != {expected_required}"

    assert path.no_of_pins == expected_no_of_pins, \
            f"Timing path {path_key} no_of_pins changed in {phase}: {path.no_of_pins} != {expected_no_of_pins}"

    assert path.is_critical_path == expected_is_critical, \
            f"Timing path {path_key} is_critical_path changed in {phase}: {path.is_critical_path} != {expected_is_critical}"


@pytest.mark.parametrize(
    "phase, expected_no_of_net_arcs",
    [
        ("floorplan", 1847),
        ("global_place", 1901),
        ("place_resized", 1832),
        ("detailed_place", 1880),
        ("cts", 2750),
        ("global_route", 2696),
        ("detailed_route", 2696),
        ("final", 2682),
    ]
)
def test_net_arc_count(dataset, phase, expected_no_of_net_arcs):
    """Track number of net arcs per stage."""
    net_arcs_df = dataset.db.get_table_data("net_arcs", flow_id=FLOW_ID, stage=phase)

    if net_arcs_df is None or len(net_arcs_df) == 0:
        pytest.skip(f"No net arcs for phase {phase}")

    actual_count = len(net_arcs_df)

    assert actual_count == expected_no_of_net_arcs, \
            f"Number of net arcs changed in {phase}: {actual_count} != {expected_no_of_net_arcs}"


@pytest.mark.parametrize(
    "phase, startpoint, endpoint, path_type, net_name, expected_values",
    [
        # Format: (phase, startpoint, endpoint, path_type, net_name, (delay, arrival_time, slew, capacitance_ff))
        # Capacitance values are in fF (femtoFarads)
        ("floorplan", "reset", "_380_/D", "hold", "_002_", (0.0384, 0.0384, 0.02115, 1.681)),
        ("floorplan", "reset", "_379_/D", "hold", "_001_", (0.03975, 0.03975, 0.01852, 1.681)),
        ("global_place", "reset", "_379_/D", "hold", "_001_", (0.04124, 0.04124, 0.02014, 2.061)),
        ("global_place", "reset", "_380_/D", "hold", "_002_", (0.04076, 0.04076, 0.02373, 2.314)),
        ("place_resized", "req_msg_3_", "_384_/D", "hold", "net26", (0.08737, 0.08737, 0.04719, 3.088)),
        ("place_resized", "req_msg_3_", "_384_/D", "hold", "_006_", (0.11101, 0.1984, 0.03602, 1.933)),
        ("detailed_place", "req_msg_14_", "_395_/D", "hold", "net6", (0.08136, 0.08136, 0.04071, 2.357)),
        ("detailed_place", "req_msg_14_", "_395_/D", "hold", "_017_", (0.11233, 0.1937, 0.0395, 2.373)),
        ("cts", "_379_/Q", "_379_/D", "hold", "clknet_0_clk", (0.121, 0.121, 0.04768, 16.63)),
        ("cts", "_379_/Q", "_379_/D", "hold", "clknet_2_3__leaf_clk", (0.1311, 0.2521, 0.05092, 18.71)),
        ("global_route", "req_msg_20_", "_401_/D", "hold", "net117", (0.191, 0.191, 0.03773, 2.601)),
        ("global_route", "req_msg_20_", "_401_/D", "hold", "net13", (0.0842, 0.2752, 0.05246, 3.571)),
        ("detailed_route", "req_msg_20_", "_401_/D", "hold", "net117", (0.191, 0.191, 0.03773, 2.601)),
        ("detailed_route", "req_msg_20_", "_401_/D", "hold", "net13", (0.0842, 0.2752, 0.05246, 3.571)),
        ("final", "req_msg_20_", "_401_/D", "hold", "net117", (0.19, 0.19, 0.03522, 2.463)),
        ("final", "req_msg_20_", "_401_/D", "hold", "net13", (0.0815, 0.2716, 0.04988, 3.337)),
    ]
)
def test_net_arc_sample_data(dataset, phase, startpoint, endpoint, path_type, net_name, expected_values):
    """Track specific net arc properties for sample arcs."""
    net_arcs_df = dataset.db.get_table_data("net_arcs", flow_id=FLOW_ID, stage=phase)

    if net_arcs_df is None or len(net_arcs_df) == 0:
        pytest.skip(f"No net arcs for phase {phase}")

    expected_delay, expected_arrival, expected_slew, expected_capacitance = expected_values

    # Find matching arc
    matching = net_arcs_df[
        (net_arcs_df.startpoint == startpoint) &
        (net_arcs_df.endpoint == endpoint) &
        (net_arcs_df.path_type == path_type) &
        (net_arcs_df.net_name == net_name)
    ]

    if len(matching) == 0:
        pytest.skip(f"Net arc ({startpoint}, {endpoint}, {path_type}, {net_name}) not found in {phase}")

    arc = matching.iloc[0]

    assert abs(arc.delay - expected_delay) < 1e-12, \
            f"Net arc ({startpoint}, {endpoint}, {path_type}, {net_name}) delay changed in {phase}: {arc.delay} != {expected_delay}"

    assert abs(arc.arrival_time - expected_arrival) < 1e-12, \
            f"Net arc ({startpoint}, {endpoint}, {path_type}, {net_name}) arrival_time changed in {phase}: {arc.arrival_time} != {expected_arrival}"

    assert abs(arc.slew - expected_slew) < 1e-12, \
            f"Net arc ({startpoint}, {endpoint}, {path_type}, {net_name}) slew changed in {phase}: {arc.slew} != {expected_slew}"

    assert abs(arc.capacitance - expected_capacitance) < 1e-6, \
            f"Net arc ({startpoint}, {endpoint}, {path_type}, {net_name}) capacitance changed in {phase}: {arc.capacitance} != {expected_capacitance}"


@pytest.mark.parametrize(
    "phase, expected_no_of_cell_arcs",
    [
        ("floorplan", 1789),
        ("global_place", 1855),
        ("place_resized", 1770),
        ("detailed_place", 1811),
        ("cts", 2654),
        ("global_route", 2606),
        ("detailed_route", 2606),
        ("final", 2593),
    ]
)
def test_cell_arc_count(dataset, phase, expected_no_of_cell_arcs):
    """Track number of cell arcs per stage."""
    cell_arcs_df = dataset.db.get_table_data("cell_arcs", flow_id=FLOW_ID, stage=phase)

    if cell_arcs_df is None or len(cell_arcs_df) == 0:
        pytest.skip(f"No cell arcs for phase {phase}")

    actual_count = len(cell_arcs_df)

    assert actual_count == expected_no_of_cell_arcs, \
            f"Number of cell arcs changed in {phase}: {actual_count} != {expected_no_of_cell_arcs}"


@pytest.mark.parametrize(
    "phase, startpoint, endpoint, path_type, gate_name, expected_values",
    [
        # Format: (phase, startpoint, endpoint, path_type, gate_name, (delay, arrival_time, slew))
        ("floorplan", "reset", "_380_/D", "hold", "_380_", (0.0, 0.0384, 0.02115)),
        ("floorplan", "reset", "_379_/D", "hold", "_379_", (0.0, 0.03975, 0.01852)),
        ("global_place", "reset", "_379_/D", "hold", "_379_", (0.0, 0.04124, 0.02014)),
        ("global_place", "reset", "_380_/D", "hold", "_380_", (0.0, 0.04076, 0.02373)),
        ("place_resized", "req_msg_3_", "_384_/D", "hold", "_279_", (2.0e-05, 0.08739, 0.04719)),
        ("place_resized", "req_msg_3_", "_384_/D", "hold", "_384_", (0.0, 0.1984, 0.03602)),
        ("detailed_place", "req_msg_14_", "_395_/D", "hold", "_301_", (1.0e-05, 0.08137, 0.04071)),
        ("detailed_place", "req_msg_14_", "_395_/D", "hold", "_395_", (0.0, 0.1937, 0.0395)),
        ("cts", "_379_/Q", "_379_/D", "hold", "clkbuf_2_3__f_clk", (0.0, 0.121, 0.04768)),
        ("cts", "_379_/Q", "_379_/D", "hold", "_379_", (0.0, 0.448, 0.07282)),
        ("global_route", "req_msg_20_", "_401_/D", "hold", "input13", (0.0, 0.191, 0.03773)),
        ("global_route", "req_msg_20_", "_401_/D", "hold", "_320_", (0.0001, 0.2753, 0.05246)),
        ("detailed_route", "req_msg_20_", "_401_/D", "hold", "input13", (0.0, 0.191, 0.03773)),
        ("detailed_route", "req_msg_20_", "_401_/D", "hold", "_320_", (0.0001, 0.2753, 0.05246)),
        ("final", "req_msg_20_", "_401_/D", "hold", "input13", (0.0001, 0.1901, 0.03522)),
        ("final", "req_msg_20_", "_401_/D", "hold", "_320_", (0.0001, 0.2717, 0.04988)),
    ]
)
def test_cell_arc_sample_data(dataset, phase, startpoint, endpoint, path_type, gate_name, expected_values):
    """Track specific cell arc properties for sample arcs."""
    cell_arcs_df = dataset.db.get_table_data("cell_arcs", flow_id=FLOW_ID, stage=phase)

    if cell_arcs_df is None or len(cell_arcs_df) == 0:
        pytest.skip(f"No cell arcs for phase {phase}")

    expected_delay, expected_arrival, expected_slew = expected_values

    # Find matching arc
    matching = cell_arcs_df[
        (cell_arcs_df.startpoint == startpoint) &
        (cell_arcs_df.endpoint == endpoint) &
        (cell_arcs_df.path_type == path_type) &
        (cell_arcs_df.gate_name == gate_name)
    ]

    if len(matching) == 0:
        pytest.skip(f"Cell arc ({startpoint}, {endpoint}, {path_type}, {gate_name}) not found in {phase}")

    arc = matching.iloc[0]

    assert abs(arc.delay - expected_delay) < 1e-12, \
            f"Cell arc ({startpoint}, {endpoint}, {path_type}, {gate_name}) delay changed in {phase}: {arc.delay} != {expected_delay}"

    assert abs(arc.arrival_time - expected_arrival) < 1e-12, \
            f"Cell arc ({startpoint}, {endpoint}, {path_type}, {gate_name}) arrival_time changed in {phase}: {arc.arrival_time} != {expected_arrival}"

    assert abs(arc.slew - expected_slew) < 1e-12, \
            f"Cell arc ({startpoint}, {endpoint}, {path_type}, {gate_name}) slew changed in {phase}: {arc.slew} != {expected_slew}"


@pytest.mark.parametrize(
    "phase, expected_values",
    [
        # Format: (phase, (routing_vdd_height, routing_vdd_width, routing_vdd_checksum, routing_vss_height, routing_vss_width, routing_vss_checksum,
        #                 ir_drop_vdd_mean, ir_drop_vdd_checksum, ir_drop_vss_mean, ir_drop_vss_checksum,
        #                 em_vdd_mean, em_vdd_checksum, em_vss_mean, em_vss_checksum))
        ("floorplan", (695, 695, 0x4fea412a, 695, 695, 0xe9d97644, None, None, None, None, None, None, None, None)),
        ("global_place", (695, 695, 0x4fea412a, 695, 695, 0xe9d97644, None, None, None, None, None, None, None, None)),
        ("place_resized", (695, 695, 0x4fea412a, 695, 695, 0xe9d97644, None, None, None, None, None, None, None, None)),
        ("detailed_place", (695, 695, 0x4fea412a, 695, 695, 0xe9d97644, None, None, None, None, None, None, None, None)),
        ("cts", (695, 695, 0x4fea412a, 695, 695, 0xe9d97644, None, None, None, None, None, None, None, None)),
        ("global_route", (695, 695, 0x4fea412a, 695, 695, 0xe9d97644, None, None, None, None, None, None, None, None)),
        ("detailed_route", (695, 695, 0x4fea412a, 695, 695, 0xe9d97644, 6.259883381927728e-05, 0x12254158, 6.933157191450751e-05, 0xb34b3fda, 7.0803323535958595e-06, 0x3afcd7c8, 7.315439070269408e-06, 0x977f27e3)),
        ("final", (695, 695, 0x4fea412a, 695, 695, 0xe9d97644, 0.00010072921132617442, 0xdc308190, 0.00012587933064521048, 0x247a753c, 8.677945374577104e-06, 0xa055c42a, 9.208549891641466e-06, 0x8c431506)),
    ]
)
def test_pdn_data(dataset, phase, expected_values):
    """Track PDN (Power Delivery Network) properties."""
    netlist = get_netlist(dataset, phase)

    if netlist.power_delivery_network is None:
        pytest.skip(f"No PDN for phase {phase}")

    pdn = netlist.power_delivery_network

    expected_routing_vdd_height, expected_routing_vdd_width, expected_routing_vdd_checksum, \
    expected_routing_vss_height, expected_routing_vss_width, expected_routing_vss_checksum, \
    expected_ir_drop_vdd_mean, expected_ir_drop_vdd_checksum, \
    expected_ir_drop_vss_mean, expected_ir_drop_vss_checksum, \
    expected_em_vdd_mean, expected_em_vdd_checksum, \
    expected_em_vss_mean, expected_em_vss_checksum = expected_values

    # Check image shapes and checksums if images exist
    if pdn.routing_vdd is not None:
        actual_shape = pdn.routing_vdd.shape
        assert actual_shape == (expected_routing_vdd_height, expected_routing_vdd_width), \
            f"PDN routing_vdd shape changed in {phase}: {actual_shape} != {(expected_routing_vdd_height, expected_routing_vdd_width)}"
        actual_checksum = zlib.crc32(pdn.routing_vdd.tobytes())
        assert actual_checksum == expected_routing_vdd_checksum, \
            f"PDN routing_vdd checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_routing_vdd_checksum:08x}"

    if pdn.routing_vss is not None:
        actual_shape = pdn.routing_vss.shape
        assert actual_shape == (expected_routing_vss_height, expected_routing_vss_width), \
            f"PDN routing_vss shape changed in {phase}: {actual_shape} != {(expected_routing_vss_height, expected_routing_vss_width)}"
        actual_checksum = zlib.crc32(pdn.routing_vss.tobytes())
        assert actual_checksum == expected_routing_vss_checksum, \
            f"PDN routing_vss checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_routing_vss_checksum:08x}"

    # Check IR drop statistics and checksums if images exist
    if pdn.ir_drop_vdd is not None:
        actual_mean = pdn.ir_drop_vdd.mean()
        assert abs(actual_mean - expected_ir_drop_vdd_mean) < 1e-6, \
            f"PDN ir_drop_vdd mean changed in {phase}: {actual_mean} != {expected_ir_drop_vdd_mean}"
        actual_checksum = zlib.crc32(pdn.ir_drop_vdd.tobytes())
        assert actual_checksum == expected_ir_drop_vdd_checksum, \
            f"PDN ir_drop_vdd checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_ir_drop_vdd_checksum:08x}"

    if pdn.ir_drop_vss is not None:
        actual_mean = pdn.ir_drop_vss.mean()
        assert abs(actual_mean - expected_ir_drop_vss_mean) < 1e-6, \
            f"PDN ir_drop_vss mean changed in {phase}: {actual_mean} != {expected_ir_drop_vss_mean}"
        actual_checksum = zlib.crc32(pdn.ir_drop_vss.tobytes())
        assert actual_checksum == expected_ir_drop_vss_checksum, \
            f"PDN ir_drop_vss checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_ir_drop_vss_checksum:08x}"

    # Check EM (electromigration) statistics and checksums if images exist
    if pdn.em_vdd is not None:
        actual_mean = pdn.em_vdd.mean()
        assert abs(actual_mean - expected_em_vdd_mean) < 1e-9, \
            f"PDN em_vdd mean changed in {phase}: {actual_mean} != {expected_em_vdd_mean}"
        actual_checksum = zlib.crc32(pdn.em_vdd.tobytes())
        assert actual_checksum == expected_em_vdd_checksum, \
            f"PDN em_vdd checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_em_vdd_checksum:08x}"

    if pdn.em_vss is not None:
        actual_mean = pdn.em_vss.mean()
        assert abs(actual_mean - expected_em_vss_mean) < 1e-9, \
            f"PDN em_vss mean changed in {phase}: {actual_mean} != {expected_em_vss_mean}"
        actual_checksum = zlib.crc32(pdn.em_vss.tobytes())
        assert actual_checksum == expected_em_vss_checksum, \
            f"PDN em_vss checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_em_vss_checksum:08x}"


@pytest.mark.parametrize(
    "phase, clock_name, image_name, expected_shape, expected_checksum",
    [
        # Format: (phase, clock_name, image_name, (height, width), checksum)
        ("global_place", "clk", "cell_placement", (695, 695), 0x309be127),
        ("global_place", "clk", "cell_placement_combinational", (695, 695), 0x0cd66938),
        ("global_place", "clk", "cell_placement_sequential", (695, 695), 0xf1066597),
        ("place_resized", "clk", "cell_placement", (695, 695), 0x530b0181),
        ("place_resized", "clk", "cell_placement_combinational", (695, 695), 0x0cd66938),
        ("place_resized", "clk", "cell_placement_sequential", (695, 695), 0x92968531),
        ("detailed_place", "clk", "cell_placement", (695, 695), 0xc0b7dcc1),
        ("detailed_place", "clk", "cell_placement_combinational", (695, 695), 0x0cd66938),
        ("detailed_place", "clk", "cell_placement_sequential", (695, 695), 0x012a5871),
        ("cts", "clk", "cell_placement", (695, 695), 0x19ee881a),
        ("cts", "clk", "cell_placement_combinational", (695, 695), 0x7ecf8c11),
        ("cts", "clk", "cell_placement_sequential", (695, 695), 0xd8730caa),
        ("global_route", "clk", "cell_placement", (695, 695), 0x19ee881a),
        ("global_route", "clk", "cell_placement_combinational", (695, 695), 0x7ecf8c11),
        ("global_route", "clk", "cell_placement_sequential", (695, 695), 0xd8730caa),
        ("detailed_route", "clk", "cell_placement", (695, 695), 0x19ee881a),
        ("detailed_route", "clk", "cell_placement_combinational", (695, 695), 0x7ecf8c11),
        ("detailed_route", "clk", "cell_placement_sequential", (695, 695), 0xd8730caa),
        ("detailed_route", "clk", "routing", (695, 695), 0x4c8e20f4),
        ("final", "clk", "cell_placement", (695, 695), 0x19ee881a),
        ("final", "clk", "cell_placement_combinational", (695, 695), 0x7ecf8c11),
        ("final", "clk", "cell_placement_sequential", (695, 695), 0xd8730caa),
        ("final", "clk", "routing", (695, 695), 0x4c8e20f4),
    ]
)
def test_clock_tree_image_data(dataset, phase, clock_name, image_name, expected_shape, expected_checksum):
    """Track clock tree image shapes and checksums for regression testing."""
    netlist = get_netlist(dataset, phase)

    if not netlist.clock_trees or clock_name not in netlist.clock_trees:
        pytest.skip(f"No clock tree '{clock_name}' for phase {phase}")

    clock_tree = netlist.clock_trees[clock_name]
    image_data = clock_tree.get_image_data()

    if image_name not in image_data or image_data[image_name] is None:
        pytest.skip(f"Clock tree image {image_name} not found in {phase}")

    img = image_data[image_name]
    actual_shape = img.shape
    expected_height, expected_width = expected_shape

    assert actual_shape == (expected_height, expected_width), \
        f"Clock tree {clock_name} image {image_name} shape changed in {phase}: {actual_shape} != {(expected_height, expected_width)}"

    actual_checksum = zlib.crc32(img.tobytes())
    assert actual_checksum == expected_checksum, \
        f"Clock tree {clock_name} image {image_name} checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_checksum:08x}"


@pytest.mark.parametrize(
    "phase, metal_layer, expected_shape, expected_checksum",
    [
        # Format: (phase, metal_layer, (height, width), checksum)
        # routing_by_metal is only available after detailed routing
        ("detailed_route", "met1", (695, 695), 0x089927d7),
        ("detailed_route", "met2", (695, 695), 0x6df04f86),
        ("detailed_route", "met3", (695, 695), 0x1f9a2adb),
        ("final", "met1", (695, 695), 0x089927d7),
        ("final", "met2", (695, 695), 0x6df04f86),
        ("final", "met3", (695, 695), 0x1f9a2adb),
    ]
)
def test_netlist_routing_by_metal_data(dataset, phase, metal_layer, expected_shape, expected_checksum):
    """Track netlist routing_by_metal image shapes and checksums for regression testing."""
    netlist = get_netlist(dataset, phase)

    if not netlist.routing_by_metal:
        pytest.skip(f"routing_by_metal not available for phase {phase}")

    if metal_layer not in netlist.routing_by_metal:
        pytest.skip(f"Metal layer {metal_layer} not found in routing_by_metal for phase {phase}")

    img = netlist.routing_by_metal[metal_layer]
    if img is None:
        pytest.skip(f"routing_by_metal[{metal_layer}] is None for phase {phase}")

    actual_shape = img.shape
    expected_height, expected_width = expected_shape

    assert actual_shape == (expected_height, expected_width), \
        f"Netlist routing_by_metal[{metal_layer}] shape changed in {phase}: {actual_shape} != {(expected_height, expected_width)}"

    actual_checksum = zlib.crc32(img.tobytes())
    assert actual_checksum == expected_checksum, \
        f"Netlist routing_by_metal[{metal_layer}] checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_checksum:08x}"


@pytest.mark.parametrize(
    "phase, clock_name, metal_layer, expected_shape, expected_checksum",
    [
        # Format: (phase, clock_name, metal_layer, (height, width), checksum)
        # routing_by_metal is only available after detailed routing
        ("detailed_route", "clk", "met1", (695, 695), 0x5b09551a),
        ("detailed_route", "clk", "met2", (695, 695), 0x2b95f13c),
        ("detailed_route", "clk", "met3", (695, 695), 0x323468bc),
        ("final", "clk", "met1", (695, 695), 0x5b09551a),
        ("final", "clk", "met2", (695, 695), 0x2b95f13c),
        ("final", "clk", "met3", (695, 695), 0x323468bc),
    ]
)
def test_clock_tree_routing_by_metal_data(dataset, phase, clock_name, metal_layer, expected_shape, expected_checksum):
    """Track clock tree routing_by_metal image shapes and checksums for regression testing."""
    netlist = get_netlist(dataset, phase)

    if not netlist.clock_trees or clock_name not in netlist.clock_trees:
        pytest.skip(f"No clock tree '{clock_name}' for phase {phase}")

    clock_tree = netlist.clock_trees[clock_name]

    if not clock_tree.routing_by_metal:
        pytest.skip(f"routing_by_metal not available for clock tree '{clock_name}' in phase {phase}")

    if metal_layer not in clock_tree.routing_by_metal:
        pytest.skip(f"Metal layer {metal_layer} not found in clock tree routing_by_metal for phase {phase}")

    img = clock_tree.routing_by_metal[metal_layer]
    if img is None:
        pytest.skip(f"Clock tree routing_by_metal[{metal_layer}] is None for phase {phase}")

    actual_shape = img.shape
    expected_height, expected_width = expected_shape

    assert actual_shape == (expected_height, expected_width), \
        f"Clock tree {clock_name} routing_by_metal[{metal_layer}] shape changed in {phase}: {actual_shape} != {(expected_height, expected_width)}"

    actual_checksum = zlib.crc32(img.tobytes())
    assert actual_checksum == expected_checksum, \
        f"Clock tree {clock_name} routing_by_metal[{metal_layer}] checksum changed in {phase}: 0x{actual_checksum:08x} != 0x{expected_checksum:08x}"


@pytest.mark.parametrize(
    "cell_name, expected_values",
    [
        # Format: (cell_name, (width, height, is_sequential, is_buffer, is_inverter, is_filler, is_tapcell))
        ("sky130_ef_sc_hd__decap_12", (5.52, 2.72, False, False, False, False, False)),
        ("sky130_ef_sc_hd__fakediode_2", (0.92, 2.72, False, False, False, False, False)),
        ("sky130_ef_sc_hd__fill_8", (3.68, 2.72, False, False, False, True, False)),
        ("sky130_ef_sc_hd__fill_12", (5.52, 2.72, False, False, False, True, False)),
        ("sky130_fd_sc_hd__a2bb2o_1", (3.68, 2.72, False, False, False, False, False)),
        ("sky130_fd_sc_hd__clkinv_1", (1.38, 2.72, False, False, True, False, False)),
        ("sky130_fd_sc_hd__buf_1", (1.38, 2.72, False, True, False, False, False)),
        ("sky130_fd_sc_hd__lpflow_inputisolatch_1", (5.06, 2.72, True, False, False, False, False)),
        ("sky130_fd_sc_hd__lpflow_lsbuf_lh_hl_isowell_tap_1", (6.44, 5.44, False, True, False, False, True)),
    ]
)
def test_standard_cell_data(dataset, cell_name, expected_values):
    """Track specific standard cell properties."""
    if cell_name not in dataset.standard_cells:
        pytest.skip(f"Standard cell {cell_name} not found")

    std_cell = dataset.standard_cells[cell_name]

    expected_width, expected_height, expected_is_sequential, expected_is_buffer, expected_is_inverter, expected_is_filler, expected_is_tapcell = expected_values

    assert abs(std_cell.width - expected_width) < 0.001, \
            f"Standard cell {cell_name} width changed: {std_cell.width} != {expected_width}"

    assert abs(std_cell.height - expected_height) < 0.001, \
            f"Standard cell {cell_name} height changed: {std_cell.height} != {expected_height}"

    assert std_cell.is_sequential == expected_is_sequential, \
            f"Standard cell {cell_name} is_sequential changed: {std_cell.is_sequential} != {expected_is_sequential}"

    assert std_cell.is_buffer == expected_is_buffer, \
            f"Standard cell {cell_name} is_buffer changed: {std_cell.is_buffer} != {expected_is_buffer}"

    assert std_cell.is_inverter == expected_is_inverter, \
            f"Standard cell {cell_name} is_inverter changed: {std_cell.is_inverter} != {expected_is_inverter}"

    assert std_cell.is_filler == expected_is_filler, \
            f"Standard cell {cell_name} is_filler changed: {std_cell.is_filler} != {expected_is_filler}"

    # is_tapcell is determined by name pattern since it's not a direct attribute
    actual_is_tapcell = ("tapvpwrvgnd" in cell_name.lower() or
                         ("tap" in cell_name.lower() and "fill" not in cell_name.lower() and "diode" not in cell_name.lower()))
    assert actual_is_tapcell == expected_is_tapcell, \
            f"Standard cell {cell_name} is_tapcell changed: {actual_is_tapcell} != {expected_is_tapcell}"


@pytest.mark.parametrize(
    "cell_name, expected_values",
    [
        # Format: (cell_name, (input_capacitance_min, input_capacitance_max, output_capacitance_min, output_capacitance_max, leakage_power_min, leakage_power_max))
        # Values are in fF (femtoFarads) for capacitance, nW (nanowatts) for leakage power
        # Leakage power: Liberty file values are in nW (per library default), no conversion needed
        ("sky130_fd_sc_hd__buf_1", (2.103, 2.103, 130.015, 130.015, 0.001181, 0.001181)),
        ("sky130_fd_sc_hd__clkinv_1", (3.077, 3.077, 190.44, 190.44, 0.0002364, 0.0028987)),
        ("sky130_fd_sc_hd__a2bb2o_1", (1.383, 1.566, 158.396, 158.396, 0.0014307, 0.0081152)),
        ("sky130_fd_sc_hd__lpflow_inputisolatch_1", (1.62, 1.652, 162.058, 162.058, 0.003234, 0.0105234)),
        ("sky130_ef_sc_hd__fill_8", (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
        ("sky130_ef_sc_hd__decap_12", (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
    ]
)
def test_standard_cell_capacitance_and_power_data(dataset, cell_name, expected_values):
    """Track standard cell capacitance and leakage power values for regression testing."""
    if cell_name not in dataset.standard_cells:
        pytest.skip(f"Standard cell {cell_name} not found")

    std_cell = dataset.standard_cells[cell_name]

    expected_input_cap_min, expected_input_cap_max, expected_output_cap_min, expected_output_cap_max, \
    expected_leakage_min, expected_leakage_max = expected_values

    # Check input capacitance (in fF)
    if expected_input_cap_min is not None:
        if std_cell.input_capacitance_min is None:
            assert False, f"Standard cell {cell_name} input_capacitance_min is None but expected {expected_input_cap_min}"
        assert abs(std_cell.input_capacitance_min - expected_input_cap_min) < 1e-3, \
                f"Standard cell {cell_name} input_capacitance_min changed: {std_cell.input_capacitance_min} != {expected_input_cap_min}"

    if expected_input_cap_max is not None:
        if std_cell.input_capacitance_max is None:
            assert False, f"Standard cell {cell_name} input_capacitance_max is None but expected {expected_input_cap_max}"
        assert abs(std_cell.input_capacitance_max - expected_input_cap_max) < 1e-3, \
                f"Standard cell {cell_name} input_capacitance_max changed: {std_cell.input_capacitance_max} != {expected_input_cap_max}"

    # Check output capacitance (in fF)
    if expected_output_cap_min is not None:
        if std_cell.output_capacitance_min is None:
            assert False, f"Standard cell {cell_name} output_capacitance_min is None but expected {expected_output_cap_min}"
        assert abs(std_cell.output_capacitance_min - expected_output_cap_min) < 1e-3, \
                f"Standard cell {cell_name} output_capacitance_min changed: {std_cell.output_capacitance_min} != {expected_output_cap_min}"

    if expected_output_cap_max is not None:
        if std_cell.output_capacitance_max is None:
            assert False, f"Standard cell {cell_name} output_capacitance_max is None but expected {expected_output_cap_max}"
        assert abs(std_cell.output_capacitance_max - expected_output_cap_max) < 1e-3, \
                f"Standard cell {cell_name} output_capacitance_max changed: {std_cell.output_capacitance_max} != {expected_output_cap_max}"

    # Check leakage power (in nW)
    if expected_leakage_min is not None:
        if std_cell.leakage_power_min is None:
            assert False, f"Standard cell {cell_name} leakage_power_min is None but expected {expected_leakage_min}"
        assert abs(std_cell.leakage_power_min - expected_leakage_min) < 1e-3, \
                f"Standard cell {cell_name} leakage_power_min changed: {std_cell.leakage_power_min} != {expected_leakage_min}"

    if expected_leakage_max is not None:
        if std_cell.leakage_power_max is None:
            assert False, f"Standard cell {cell_name} leakage_power_max is None but expected {expected_leakage_max}"
        assert abs(std_cell.leakage_power_max - expected_leakage_max) < 1e-3, \
                f"Standard cell {cell_name} leakage_power_max changed: {std_cell.leakage_power_max} != {expected_leakage_max}"

