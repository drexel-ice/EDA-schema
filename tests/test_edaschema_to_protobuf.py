"""
EDA Schema to Protocol Buffers Conversion Test Suite

This test suite validates the serialization and deserialization of EDA schema objects 
to and from Protocol Buffers format. It ensures that all relevant data is preserved
correctly during the conversion process.

Tests include:
- Loading EDA schema datasets
- Converting dataset objects to Protocol Buffers
- Saving Protocol Buffers to files
- Loading Protocol Buffers from files
- Comparing original and deserialized data for equality

The test suite verifies the following components:
- Basic netlist attributes (dimensions, utilization, densities)
- Cell metrics (counts of different cell types)
- Area metrics (area measurements for various components)
- Power metrics (power consumption measurements)
- Critical path metrics (timing information)
- Timing path data

Requirements:
- pytest
- EDA schema library with protobuf_io module
- Test dataset directory structure with sample netlists

Usage:
    pytest -v tests/test_edaschema_to_protobuf.py
"""

import os
import pytest
import tempfile
from eda_schema.entity import PHASES, NetlistEntity
from eda_schema.dataset import Dataset
from eda_schema.db import SQLitePickleDB
from eda_schema.protobuf_io import save_protobuf_file, dataset_to_protobuf, load_protobuf_file, protobuf_to_dataset

# Constants
DATASET_DIR = "dataset/test"
NETLIST_ID = 'id-000001'

@pytest.fixture
def test_dataset():
    """Fixture to load the dataset once for all tests."""
    dataset = Dataset(SQLitePickleDB(DATASET_DIR))
    dataset.load_standard_cells()
    dataset.load_dataset(netlist_id=NETLIST_ID)
    return dataset

@pytest.fixture
def first_netlist(test_dataset):
    """Fixture to get the first netlist from the dataset."""
    for netlist_key, netlist in test_dataset.items():
        return netlist_key, netlist
    pytest.fail("No netlist found in dataset")

@pytest.fixture
def temp_protobuf_file():
    """Fixture to create a temporary file for protobuf data."""
    with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as tmp_file:
        filename = tmp_file.name
    
    yield filename  # Provide the filename to the test
    
    # Cleanup after the test
    if os.path.exists(filename):
        os.remove(filename)

def test_load_dataset():
    """Test loading dataset."""
    dataset = Dataset(SQLitePickleDB(DATASET_DIR))
    dataset.load_standard_cells()
    dataset.load_dataset(netlist_id=NETLIST_ID)
    
    assert len(dataset) > 0, "Dataset should contain at least one netlist"
    
    # Check if standard cells were loaded
    assert len(dataset.standard_cells) > 0, "Standard cells should be loaded"
    
    # Check if the netlist with the specified ID was loaded
    netlists = list(dataset.keys())
    found = False
    for netlist_key in netlists:
        if isinstance(netlist_key, tuple) and NETLIST_ID in netlist_key:
            found = True
            break
    assert found, f"Netlist with ID {NETLIST_ID} not found in dataset"


def is_proto_edaschema_equal(proto_obj, edaschema_entity):
    """Check if the protobuf file and EDA schema entity are equal.

    NOTE: This comparison uses rounding due to known precision differences
    between Protobuf (float32) and JSON Schema (usually float64).
    Increasing the rounding precision (e.g., from 2 to 4) may cause test
    failures due to small discrepancies in float representation.
    """
    is_match = True
    for attr, attr_meta in edaschema_entity.schema["items"]["properties"].items():
        # HACK: skip sort_index for now — needs upstream fix in EDA-schema
        if attr in ["sort_index", "rudy"]:
            continue
        attr_is_numeric = attr_meta["type"] == "number" or (isinstance(attr_meta["type"], list) and "number" in attr_meta["type"])
        if attr_is_numeric:
            # TODO: Properly handle nullable fields (e.g., FloatValue) once unwrapping is in place.
            # For now, default to 0.0 when EDA-schema field is None/missing
            is_match = is_match and round(float(getattr(proto_obj, attr)), 2) == round(float(getattr(edaschema_entity, attr) or 0), 2)
            # print(is_match, attr, getattr(proto_obj, attr), getattr(edaschema_entity, attr) or 0)
        elif attr == "standard_cell":
            is_match = is_match and getattr(proto_obj, attr).name == getattr(edaschema_entity, attr)
        else:
            is_match = is_match and getattr(proto_obj, attr) == getattr(edaschema_entity, attr)
            # print(is_match, attr, getattr(proto_obj, attr), getattr(edaschema_entity, attr) or 0)
    return is_match


def test_convert_dataset_to_protobuf(test_dataset, first_netlist, temp_protobuf_file):
    """Test converting dataset to protobuf format and saving to file."""
    netlist_key, netlist = first_netlist

    # Convert the netlist to protobuf
    netlist_proto = dataset_to_protobuf(test_dataset, netlist)

    # Top-level comparisons
    assert is_proto_edaschema_equal(netlist_proto, netlist)
    assert is_proto_edaschema_equal(netlist_proto.cell_metrics, netlist.cell_metrics)
    assert is_proto_edaschema_equal(netlist_proto.area_metrics, netlist.area_metrics)
    assert is_proto_edaschema_equal(netlist_proto.power_metrics, netlist.power_metrics)
    assert is_proto_edaschema_equal(netlist_proto.critical_path_metrics, netlist.critical_path_metrics)

    # Check timing paths
    for i, timing_path in enumerate(netlist.timing_paths.values()):
        timing_path_proto = netlist_proto.timing_paths[i]
        assert is_proto_edaschema_equal(timing_path_proto, timing_path[0])

    # Check clock trees
    for i, clock_tree in enumerate(netlist.clock_trees.values()):
        clock_tree_proto = netlist_proto.clock_trees[i]
        assert is_proto_edaschema_equal(clock_tree_proto, clock_tree)

    io_port_index, gate_index, interconnect_index = 0, 0, 0
    for node in netlist:
        node_type = netlist.nodes[node]['type']
        node_entity = netlist.nodes[node]['entity']
        if node_type == 'IO_PORT':
            node_proto = netlist_proto.io_ports[io_port_index]
            io_port_index += 1
            assert is_proto_edaschema_equal(node_proto, node_entity)
        elif node_type == 'GATE':
            node_proto = netlist_proto.gates[gate_index]
            gate_index += 1
            assert is_proto_edaschema_equal(node_proto, node_entity)
        elif node_type == 'INTERCONNECT':
            node_proto = netlist_proto.interconnects[interconnect_index]
            interconnect_index += 1
            assert is_proto_edaschema_equal(node_proto, node_entity)

    for edge_index, edges in enumerate(netlist.edges):
        edge1, edge2 = edges
        edge_proto = netlist_proto.edges[edge_index]
        assert edge_proto.source == edge1
        assert edge_proto.target == edge2

    # Check if conversion was successful
    assert netlist_proto is not None, "Conversion to protobuf failed"
    assert netlist_proto.ByteSize() > 0, "Protobuf data should not be empty"
    
    # Save the protobuf data to file
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Check if file was created and has content
    assert os.path.exists(temp_protobuf_file), "Protobuf file was not created"
    assert os.path.getsize(temp_protobuf_file) > 0, "Protobuf file is empty"

def test_load_protobuf_file(test_dataset, first_netlist, temp_protobuf_file):
    """Test loading protobuf data from file."""
    netlist_key, netlist = first_netlist
    
    # Convert and save first
    netlist_proto = dataset_to_protobuf(netlist)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Load the protobuf data
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Check if loading was successful
    assert loaded_proto is not None, "Failed to load protobuf file"
    assert loaded_proto.ByteSize() > 0, "Loaded protobuf data should not be empty"
    assert loaded_proto.ByteSize() == netlist_proto.ByteSize(), "Loaded data size doesn't match original"

def verify_attribute_equality(netlist_val, protobuf_val, attr_name):
    """Helper function to verify equality with appropriate handling for floats."""
    if isinstance(netlist_val, float) and isinstance(protobuf_val, float):
        assert abs(netlist_val - protobuf_val) < 0.001, f"Float values for {attr_name} do not match"
    else:
        assert netlist_val == protobuf_val, f"Values for {attr_name} do not match"

def test_basic_attributes_equality(test_dataset, first_netlist, temp_protobuf_file):
    """Test that basic netlist attributes match between dataset and protobuf."""
    netlist_key, netlist = first_netlist
    
    # Convert and save
    netlist_proto = dataset_to_protobuf(netlist)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Load the protobuf data
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Check basic attributes
    basic_attrs = [
        'width', 'height', 'no_of_inputs', 'no_of_outputs', 
        'utilization', 'cell_density', 'pin_density', 'net_density'
    ]
    
    for attr in basic_attrs:
        if hasattr(netlist, attr) and hasattr(loaded_proto, attr):
            netlist_val = getattr(netlist, attr)
            protobuf_val = getattr(loaded_proto, attr)
            verify_attribute_equality(netlist_val, protobuf_val, attr)

def test_cell_metrics_equality(test_dataset, first_netlist, temp_protobuf_file):
    """Test that cell metrics match between dataset and protobuf."""
    netlist_key, netlist = first_netlist
    
    # Skip if netlist doesn't have cell metrics
    if not hasattr(netlist, 'cell_metrics'):
        pytest.skip("Netlist doesn't have cell metrics")
    
    # Convert and save
    netlist_proto = dataset_to_protobuf(netlist)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Load the protobuf data
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Check cell metrics
    assert hasattr(loaded_proto, 'cell_metrics'), "Loaded protobuf should have cell_metrics"
    
    cm_attrs = [
        'no_of_combinational_cells', 'no_of_sequential_cells',
        'no_of_buffers', 'no_of_inverters', 'no_of_fillers',
        'no_of_tap_cells', 'no_of_diodes', 'no_of_macros',
        'no_of_total_cells'
    ]
    
    for attr in cm_attrs:
        if hasattr(netlist.cell_metrics, attr) and hasattr(loaded_proto.cell_metrics, attr):
            netlist_val = getattr(netlist.cell_metrics, attr)
            protobuf_val = getattr(loaded_proto.cell_metrics, attr)
            verify_attribute_equality(netlist_val, protobuf_val, f"cell_metrics.{attr}")

def test_area_metrics_equality(test_dataset, first_netlist, temp_protobuf_file):
    """Test that area metrics match between dataset and protobuf."""
    netlist_key, netlist = first_netlist
    
    # Skip if netlist doesn't have area metrics
    if not hasattr(netlist, 'area_metrics'):
        pytest.skip("Netlist doesn't have area metrics")
    
    # Convert and save
    netlist_proto = dataset_to_protobuf(netlist)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Load the protobuf data
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Check area metrics
    assert hasattr(loaded_proto, 'area_metrics'), "Loaded protobuf should have area_metrics"
    
    am_attrs = [
        'combinational_cell_area', 'sequential_cell_area', 'buffer_area',
        'inverter_area', 'filler_area', 'tap_cell_area', 'diode_area',
        'macro_area', 'cell_area', 'total_area'
    ]
    
    for attr in am_attrs:
        if hasattr(netlist.area_metrics, attr) and hasattr(loaded_proto.area_metrics, attr):
            netlist_val = getattr(netlist.area_metrics, attr)
            protobuf_val = getattr(loaded_proto.area_metrics, attr)
            verify_attribute_equality(netlist_val, protobuf_val, f"area_metrics.{attr}")

def test_power_metrics_equality(test_dataset, first_netlist, temp_protobuf_file):
    """Test that power metrics match between dataset and protobuf."""
    netlist_key, netlist = first_netlist
    
    # Skip if netlist doesn't have power metrics
    if not hasattr(netlist, 'power_metrics'):
        pytest.skip("Netlist doesn't have power metrics")
    
    # Convert and save
    netlist_proto = dataset_to_protobuf(netlist)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Load the protobuf data
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Check power metrics
    assert hasattr(loaded_proto, 'power_metrics'), "Loaded protobuf should have power_metrics"
    
    pm_attrs = [
        'combinational_power', 'sequential_power', 'macro_power',
        'internal_power', 'switching_power', 'leakage_power', 'total_power'
    ]
    
    for attr in pm_attrs:
        if hasattr(netlist.power_metrics, attr) and hasattr(loaded_proto.power_metrics, attr):
            netlist_val = getattr(netlist.power_metrics, attr)
            protobuf_val = getattr(loaded_proto.power_metrics, attr)
            verify_attribute_equality(netlist_val, protobuf_val, f"power_metrics.{attr}")

def test_critical_path_metrics_equality(test_dataset, first_netlist, temp_protobuf_file):
    """Test that critical path metrics match between dataset and protobuf."""
    netlist_key, netlist = first_netlist
    
    # Skip if netlist doesn't have critical path metrics
    if not hasattr(netlist, 'critical_path_metrics'):
        pytest.skip("Netlist doesn't have critical path metrics")
    
    # Convert and save
    netlist_proto = dataset_to_protobuf(netlist)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Load the protobuf data
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Check critical path metrics
    assert hasattr(loaded_proto, 'critical_path_metrics'), "Loaded protobuf should have critical_path_metrics"
    
    cpm_attrs = [
        'startpoint', 'endpoint', 'worst_arrival_time', 'worst_slack',
        'total_negative_slack', 'no_of_timing_paths', 'no_of_slack_violations'
    ]
    
    for attr in cpm_attrs:
        if hasattr(netlist.critical_path_metrics, attr) and hasattr(loaded_proto.critical_path_metrics, attr):
            netlist_val = getattr(netlist.critical_path_metrics, attr)
            protobuf_val = getattr(loaded_proto.critical_path_metrics, attr)
            verify_attribute_equality(netlist_val, protobuf_val, f"critical_path_metrics.{attr}")

def test_timing_paths_count(test_dataset, first_netlist, temp_protobuf_file):
    """Test that timing paths count matches between dataset and protobuf."""
    netlist_key, netlist = first_netlist
    
    # Skip if netlist doesn't have timing paths
    if not hasattr(netlist, 'timing_paths'):
        pytest.skip("Netlist doesn't have timing paths")
    
    # Convert and save
    netlist_proto = dataset_to_protobuf(netlist)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Load the protobuf data
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Check timing paths count
    assert hasattr(loaded_proto, 'timing_paths'), "Loaded protobuf should have timing_paths"
    
    netlist_timing_path_count = sum(len(paths) for paths in netlist.timing_paths.values())
    protobuf_timing_path_count = len(loaded_proto.timing_paths)
    
    assert netlist_timing_path_count == protobuf_timing_path_count, "Timing path count doesn't match"

def test_end_to_end_conversion(test_dataset, first_netlist, temp_protobuf_file):
    """Test the entire process of converting to protobuf and back."""
    netlist_key, netlist = first_netlist
    
    # Convert netlist to protobuf
    netlist_proto = dataset_to_protobuf(netlist)
    
    # Save protobuf to file
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Read back from file
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Verify size matches
    assert loaded_proto.ByteSize() == netlist_proto.ByteSize(), "Protobuf size mismatch after save/load cycle"
    
    # Verify a sample of attributes from different sections
    # Basic attribute
    if hasattr(netlist, 'width'):
        verify_attribute_equality(netlist.width, loaded_proto.width, "width")
    
    # Cell metrics
    if hasattr(netlist, 'cell_metrics') and hasattr(netlist.cell_metrics, 'no_of_total_cells'):
        verify_attribute_equality(
            netlist.cell_metrics.no_of_total_cells, 
            loaded_proto.cell_metrics.no_of_total_cells,
            "cell_metrics.no_of_total_cells"
        )
    
    # Area metrics
    if hasattr(netlist, 'area_metrics') and hasattr(netlist.area_metrics, 'total_area'):
        verify_attribute_equality(
            netlist.area_metrics.total_area, 
            loaded_proto.area_metrics.total_area,
            "area_metrics.total_area"
        )
    
    # Power metrics
    if hasattr(netlist, 'power_metrics') and hasattr(netlist.power_metrics, 'total_power'):
        verify_attribute_equality(
            netlist.power_metrics.total_power, 
            loaded_proto.power_metrics.total_power,
            "power_metrics.total_power"
        )

def test_protobuf_to_dataset(test_dataset, first_netlist, temp_protobuf_file):
    """Test converting protobuf back to dataset."""
    netlist_key, netlist = first_netlist
    
    # Manually add circuit, netlist_id and phase for testing purposes
    if not hasattr(netlist, 'circuit'):
        netlist.circuit = netlist_key[0]
    if not hasattr(netlist, 'netlist_id'):
        netlist.netlist_id = netlist_key[1]
    if not hasattr(netlist, 'phase'):
        netlist.phase = netlist_key[2]

    # Convert netlist to protobuf
    netlist_proto = dataset_to_protobuf(netlist)
    
    # Save protobuf to file
    with open(temp_protobuf_file, 'wb') as f:
        f.write(netlist_proto.SerializeToString())
    
    # Load protobuf from file
    loaded_proto = load_protobuf_file(temp_protobuf_file)
    
    # Convert protobuf back to dataset
    reconstructed_dataset = protobuf_to_dataset(loaded_proto, test_dataset.db)

    # Verify the reconstructed dataset contains the original netlist key
    assert netlist_key in reconstructed_dataset, "Reconstructed dataset is missing the original netlist key"

    reconstructed_netlist = reconstructed_dataset[netlist_key]

    # Verify basic attributes
    for attr in ['width', 'height', 'no_of_inputs', 'no_of_outputs', 'utilization']:
        if attr in netlist:
            original_value = netlist[attr]
            reconstructed_value = reconstructed_netlist[attr]
            verify_attribute_equality(original_value, reconstructed_value, attr)

    # Verify cell metrics
    if 'cell_metrics' in netlist:
        for attr in ['no_of_combinational_cells', 'no_of_sequential_cells', 'no_of_total_cells']:
            if attr in netlist['cell_metrics']:
                original_value = netlist['cell_metrics'][attr]
                reconstructed_value = reconstructed_netlist['cell_metrics'][attr]
                verify_attribute_equality(original_value, reconstructed_value, f"cell_metrics.{attr}")

    # Verify area metrics
    if 'area_metrics' in netlist:
        for attr in ['total_area', 'cell_area']:
            if attr in netlist['area_metrics']:
                original_value = netlist['area_metrics'][attr]
                reconstructed_value = reconstructed_netlist['area_metrics'][attr]
                verify_attribute_equality(original_value, reconstructed_value, f"area_metrics.{attr}")

    # Verify power metrics
    if 'power_metrics' in netlist:
        for attr in ['total_power', 'internal_power']:
            if attr in netlist['power_metrics']:
                original_value = netlist['power_metrics'][attr]
                reconstructed_value = reconstructed_netlist['power_metrics'][attr]
                verify_attribute_equality(original_value, reconstructed_value, f"power_metrics.{attr}")

    # Verify timing paths count
    if 'timing_paths' in netlist:
        original_count = sum(len(paths) for paths in netlist['timing_paths'].values())
        reconstructed_count = sum(len(paths) for paths in reconstructed_netlist['timing_paths'].values())
        assert original_count == reconstructed_count, "Timing paths count mismatch"
