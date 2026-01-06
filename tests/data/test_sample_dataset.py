import pytest
from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB

DATASET_DIR = "dataset/test"
FLOW_ID = 'gcd-000001'


@pytest.fixture(scope="module")
def dataset():
    """Load dataset once per test module."""
    dataset = Dataset(ParquetDB(DATASET_DIR))
    dataset.load(flow_id=FLOW_ID)
    return dataset


def get_netlist(dataset, phase):
    """Helper function to get netlist for a phase."""
    flow = dataset[FLOW_ID]
    return flow.stages[phase].netlist

@pytest.mark.parametrize(
    "phase, expected_values",
    [
        ("floorplan", (312, 272, 36, 18, 0, 20, 41)),
        ("global_place", (213, 272, 36, 18, 0, 20, 41)),
        ("place_resized", (266, 325, 36, 18, 53, 20, 41)),
        ("detailed_place", (266, 325, 36, 18, 53, 20, 41)),
        ("cts", (340, 399, 36, 18, 61, 20, 41)),
        ("global_route", (354, 413, 36, 18, 126, 20, 41)),
        ("detailed_route", (1006, 413, 36, 18, 126, 20, 41)),
        ("final", (1006, 413, 36, 18, 126, 20, 41)),
    ]
)
def test_netlist_sanity_check(dataset, phase, expected_values):
    expected_no_of_cells, expected_no_of_nets, expected_no_of_inputs, expected_no_of_outputs, \
    expected_no_of_buffer, expected_no_of_inverter, expected_no_of_sequential = expected_values

    netlist = get_netlist(dataset, phase)

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

@pytest.mark.parametrize(
    "phase, expected_no_of_buffers, expected_no_of_clock_sinks, expected_no_of_nets",
    [
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
    netlist = get_netlist(dataset, phase)
    clock_tree = netlist.clock_trees["clk"]

    no_of_nets = sum(1 for node in clock_tree.nodes if netlist.nodes[node]["type"] == "NET")

    assert clock_tree.no_of_buffers == expected_no_of_buffers
    assert clock_tree.no_of_clock_sinks == expected_no_of_clock_sinks
    assert no_of_nets == expected_no_of_nets
