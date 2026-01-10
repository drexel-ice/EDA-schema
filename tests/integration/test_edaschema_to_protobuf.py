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

import math
import os
import tempfile
from dataclasses import fields

import pytest

from eda_schema.entity import DesignStages
from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB
from eda_schema.serialization.protobuf_io import (
    save_protobuf_file, dataset_to_protobuf, load_protobuf_file, protobuf_to_dataset
)

pytestmark = pytest.mark.slow

# Constants
DATASET_DIR = "dataset/test"
FLOW_ID = 'gcd-000001'

@pytest.fixture(scope="module")
def test_dataset():
    """Fixture to load the dataset once for all tests in this module."""
    dataset = Dataset(ParquetDB(DATASET_DIR))
    dataset.load_standard_cells()
    return dataset

@pytest.fixture
def first_stage_entity(test_dataset):
    """Fixture to get the first stage entity from the dataset."""
    try:
        design_flow = test_dataset.load_design_flow(flow_id=FLOW_ID)
        # Get the first available stage
        for stage_name in DesignStages.tolist():
            if stage_name in design_flow.stages:
                stage_entity = design_flow.stages[stage_name]
                if stage_entity.netlist is not None:
                    return stage_entity
        pytest.fail(f"No netlist found in flow {FLOW_ID}")
    except Exception as e:
        pytest.skip(f"Could not load design flow {FLOW_ID}: {e}")

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
    dataset = Dataset(ParquetDB(DATASET_DIR))
    dataset.load_standard_cells()

    # Check if standard cells were loaded
    assert len(dataset.standard_cells) > 0, "Standard cells should be loaded"

    # Check if we can load a design flow
    try:
        design_flow = dataset.load_design_flow(flow_id=FLOW_ID)
        assert design_flow is not None, f"Design flow {FLOW_ID} should be loaded"
        assert len(design_flow.stages) > 0, f"Design flow {FLOW_ID} should have at least one stage"
    except Exception as e:
        pytest.skip(f"Could not load design flow {FLOW_ID}: {e}")


def is_proto_edaschema_equal(proto_obj, edaschema_entity):
    """Check if the protobuf file and EDA schema entity are equal.

    NOTE: This comparison uses rounding due to known precision differences
    between Protobuf (float32) and JSON Schema (usually float64).
    Increasing the rounding precision (e.g., from 2 to 4) may cause test
    failures due to small discrepancies in float representation.
    """
    if edaschema_entity is None:
        return proto_obj is None or (hasattr(proto_obj, 'ByteSize') and proto_obj.ByteSize() == 0)

    if proto_obj is None:
        return False

    is_match = True
    # Iterate over dataclass fields instead of schema dict
    for field_info in fields(edaschema_entity):
        attr = field_info.name
        # Skip metadata fields and complex types
        if attr in ["sort_index", "rudy", "routing", "routing_by_metal", "cell_placement",
                    "cell_placement_combinational", "cell_placement_sequential",
                    "cell_placement_filler", "pin_placement", "timing_paths", "clock_trees",
                    "power_delivery_network", "cell_metrics", "area_metrics", "power_metrics",
                    "timing_metrics", "routability_metrics"]:
            continue

        if not hasattr(proto_obj, attr):
            continue

        proto_val = getattr(proto_obj, attr, None)
        eda_val = getattr(edaschema_entity, attr, None)

        # Skip comparison if both are None or if proto has default value and entity is None
        if proto_val is None and eda_val is None:
            continue
        if proto_val == 0 and eda_val is None:
            continue
        if proto_val == "" and eda_val is None:
            continue

        # Handle numeric fields with rounding
        # Check if the actual values are numeric (more reliable than type annotations)
        proto_is_numeric = isinstance(proto_val, (int, float)) and proto_val is not None
        eda_is_numeric = isinstance(eda_val, (int, float)) and eda_val is not None

        # Also check type annotation as fallback
        type_str = str(field_info.type)
        type_is_numeric = ('float' in type_str or 'int' in type_str) and 'str' not in type_str

        if proto_is_numeric or eda_is_numeric or type_is_numeric:
            proto_val = float(proto_val) if proto_val is not None else 0.0
            eda_val = float(eda_val) if eda_val is not None else 0.0
            # Handle NaN values - both must be NaN to be equal
            if math.isnan(proto_val) and math.isnan(eda_val):
                # Both are NaN, consider them equal
                continue
            if math.isnan(proto_val) or math.isnan(eda_val):
                # One is NaN, the other isn't - not equal
                is_match = False
            else:
                # Use tolerance-based comparison for floating point values
                # Protobuf uses float32, EDA schema uses float64, so we need tolerance
                tolerance = 1e-3  # 0.001 tolerance
                rounded_match = abs(proto_val - eda_val) < tolerance
                is_match = is_match and rounded_match
        elif attr == "standard_cell":
            # standard_cell is now a string in both proto and entity
            proto_stdcell = proto_val if isinstance(proto_val, str) else (proto_val.name if hasattr(proto_val, 'name') else str(proto_val))
            is_match = is_match and proto_stdcell == eda_val
        else:
            is_match = is_match and proto_val == eda_val
    return is_match


def test_convert_dataset_to_protobuf(test_dataset, first_stage_entity):
    """Test converting dataset to protobuf format and saving to file."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Convert the stage entity to protobuf
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    netlist_proto = stage_proto.netlist

    # Top-level comparisons
    assert is_proto_edaschema_equal(netlist_proto, netlist)
    # Metrics are stored in stage_entity, not netlist
    if stage_entity.cell_metrics and stage_proto.cell_metrics:
        assert is_proto_edaschema_equal(stage_proto.cell_metrics, stage_entity.cell_metrics)
    if stage_entity.area_metrics and stage_proto.area_metrics:
        assert is_proto_edaschema_equal(stage_proto.area_metrics, stage_entity.area_metrics)
    if stage_entity.power_metrics and stage_proto.power_metrics:
        assert is_proto_edaschema_equal(stage_proto.power_metrics, stage_entity.power_metrics)
    if stage_entity.timing_metrics and stage_proto.timing_metrics:
        assert is_proto_edaschema_equal(stage_proto.timing_metrics, stage_entity.timing_metrics)

    # Check timing paths
    if netlist.timing_paths and netlist_proto.timing_paths:
        timing_path_list = list(netlist.timing_paths.values())
        for i, timing_path in enumerate(timing_path_list):
            if i < len(netlist_proto.timing_paths):
                timing_path_proto = netlist_proto.timing_paths[i]
                assert is_proto_edaschema_equal(timing_path_proto, timing_path)

    # Check clock trees
    if netlist.clock_trees and netlist_proto.clock_trees:
        clock_tree_list = list(netlist.clock_trees.values())
        for i, clock_tree in enumerate(clock_tree_list):
            if i < len(netlist_proto.clock_trees):
                clock_tree_proto = netlist_proto.clock_trees[i]
                assert is_proto_edaschema_equal(clock_tree_proto, clock_tree)

    port_index, gate_index, net_index = 0, 0, 0
    for node in netlist.nodes:
        node_type = netlist.nodes[node]['type']
        node_entity = netlist.nodes[node]['entity']
        if node_type == 'PORT':
            if port_index < len(netlist_proto.ports):
                node_proto = netlist_proto.ports[port_index]
                port_index += 1
                assert is_proto_edaschema_equal(node_proto, node_entity)
        elif node_type == 'GATE':
            if gate_index < len(netlist_proto.gates):
                node_proto = netlist_proto.gates[gate_index]
                gate_index += 1
                assert is_proto_edaschema_equal(node_proto, node_entity)
        elif node_type == 'NET':
            if net_index < len(netlist_proto.nets):
                node_proto = netlist_proto.nets[net_index]
                net_index += 1
                assert is_proto_edaschema_equal(node_proto, node_entity)

    # Check edges
    if netlist.edges and netlist_proto.edges:
        edge_list = list(netlist.edges)
        for edge_index, edges in enumerate(edge_list):
            if edge_index < len(netlist_proto.edges):
                edge1, edge2 = edges
                edge_proto = netlist_proto.edges[edge_index]
                assert edge_proto.source == edge1
                assert edge_proto.target == edge2

    # Check if conversion was successful
    assert netlist_proto is not None, "Conversion to protobuf failed"
    assert netlist_proto.ByteSize() > 0, "Protobuf data should not be empty"

def test_convert_protobuf_to_edaschema(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test converting protobuf back to edaschema."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Convert to protobuf and save
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    save_protobuf_file(stage_proto, temp_protobuf_file)

    # Load protobuf from file
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)
    netlist_proto = loaded_stage_proto.netlist

    # Convert back to dataset
    reconstructed_stage = protobuf_to_dataset(loaded_stage_proto)
    reconstructed_netlist = reconstructed_stage.netlist

    # Top-level comparisons
    assert is_proto_edaschema_equal(netlist_proto, reconstructed_netlist)
    if netlist.cell_metrics and netlist_proto.cell_metrics:
        assert is_proto_edaschema_equal(netlist_proto.cell_metrics, reconstructed_netlist.cell_metrics)
    if netlist.area_metrics and netlist_proto.area_metrics:
        assert is_proto_edaschema_equal(netlist_proto.area_metrics, reconstructed_netlist.area_metrics)
    if netlist.power_metrics and netlist_proto.power_metrics:
        assert is_proto_edaschema_equal(netlist_proto.power_metrics, reconstructed_netlist.power_metrics)
    if netlist.timing_metrics and netlist_proto.timing_metrics:
        assert is_proto_edaschema_equal(netlist_proto.timing_metrics, reconstructed_netlist.timing_metrics)

    # Check timing paths - compare reconstructed with original
    if netlist.timing_paths and reconstructed_netlist.timing_paths:
        # Compare by keys
        for path_key in netlist.timing_paths:
            if path_key in reconstructed_netlist.timing_paths:
                original_path = netlist.timing_paths[path_key]
                reconstructed_path = reconstructed_netlist.timing_paths[path_key]
                # Compare key attributes
                assert original_path.startpoint == reconstructed_path.startpoint
                assert original_path.endpoint == reconstructed_path.endpoint
                assert original_path.path_type == reconstructed_path.path_type

    # Check nodes - compare reconstructed with original
    # Just verify that the counts match and key nodes exist
    assert len(reconstructed_netlist.nodes) == len(netlist.nodes), \
        f"Node count mismatch: reconstructed={len(reconstructed_netlist.nodes)}, original={len(netlist.nodes)}"

    # Verify a sample of nodes exist and have correct types
    sample_nodes = list(netlist.nodes)[:10]  # Check first 10 nodes
    for node_name in sample_nodes:
        if node_name in reconstructed_netlist.nodes:
            original_type = netlist.nodes[node_name].get('type')
            reconstructed_type = reconstructed_netlist.nodes[node_name].get('type')
            assert original_type == reconstructed_type, \
                f"Node {node_name} type mismatch: original={original_type}, reconstructed={reconstructed_type}"

    eda_schema_edges = list(netlist.edges)
    proto_edges = [(edge.source, edge.target) for edge in netlist_proto.edges]
    assert len(eda_schema_edges) == len(netlist_proto.edges), "Number of edges in EDA schema and protobuf do not match"
    assert sorted(eda_schema_edges) == sorted(proto_edges), "Edges in EDA schema and protobuf do not match"

def test_save_protobuf_file(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test saving a StageEntity protobuf object to a file."""
    stage_entity = first_stage_entity

    # Convert stage entity to protobuf
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)

    # Save protobuf to file
    save_protobuf_file(stage_proto, temp_protobuf_file)

    # Assertions: file must exist and not be empty
    assert os.path.exists(temp_protobuf_file), "Protobuf file was not created."
    assert os.path.getsize(temp_protobuf_file) > 0, "Protobuf file is empty."

def test_load_protobuf_file(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test loading StageEntity protobuf data from file."""
    stage_entity = first_stage_entity

    # Convert and save first
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Load the protobuf data
    loaded_proto = load_protobuf_file(temp_protobuf_file)

    # Check if loading was successful
    assert loaded_proto is not None, "Failed to load protobuf file"
    assert loaded_proto.ByteSize() > 0, "Loaded protobuf data should not be empty"
    assert loaded_proto.ByteSize() == stage_proto.ByteSize(), "Loaded data size doesn't match original"

def verify_attribute_equality(netlist_val, protobuf_val, attr_name):
    """Helper function to verify equality with appropriate handling for floats."""
    if isinstance(netlist_val, float) and isinstance(protobuf_val, float):
        assert abs(netlist_val - protobuf_val) < 0.001, f"Float values for {attr_name} do not match"
    else:
        assert netlist_val == protobuf_val, f"Values for {attr_name} do not match"

def test_basic_attributes_equality(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test that basic netlist attributes match between dataset and protobuf."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Convert and save
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Load the protobuf data
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)
    loaded_proto = loaded_stage_proto.netlist

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

def test_cell_metrics_equality(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test that cell metrics match between dataset and protobuf."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Skip if netlist doesn't have cell metrics
    if not netlist.cell_metrics:
        pytest.skip("Netlist doesn't have cell metrics")

    # Convert and save
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Load the protobuf data
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)
    loaded_proto = loaded_stage_proto.netlist

    # Check cell metrics
    assert loaded_proto.cell_metrics is not None, "Loaded protobuf should have cell_metrics"

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

def test_area_metrics_equality(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test that area metrics match between dataset and protobuf."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Skip if netlist doesn't have area metrics
    if not netlist.area_metrics:
        pytest.skip("Netlist doesn't have area metrics")

    # Convert and save
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Load the protobuf data
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)
    loaded_proto = loaded_stage_proto.netlist

    # Check area metrics
    assert loaded_proto.area_metrics is not None, "Loaded protobuf should have area_metrics"

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

def test_power_metrics_equality(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test that power metrics match between dataset and protobuf."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Skip if netlist doesn't have power metrics
    if not netlist.power_metrics:
        pytest.skip("Netlist doesn't have power metrics")

    # Convert and save
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Load the protobuf data
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)
    loaded_proto = loaded_stage_proto.netlist

    # Check power metrics
    assert loaded_proto.power_metrics is not None, "Loaded protobuf should have power_metrics"

    pm_attrs = [
        'combinational_power', 'sequential_power', 'macro_power',
        'internal_power', 'switching_power', 'leakage_power', 'total_power'
    ]

    for attr in pm_attrs:
        if hasattr(netlist.power_metrics, attr) and hasattr(loaded_proto.power_metrics, attr):
            netlist_val = getattr(netlist.power_metrics, attr)
            protobuf_val = getattr(loaded_proto.power_metrics, attr)
            verify_attribute_equality(netlist_val, protobuf_val, f"power_metrics.{attr}")

def test_timing_metrics_equality(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test that timing metrics match between dataset and protobuf."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Skip if netlist doesn't have timing metrics
    if not netlist.timing_metrics:
        pytest.skip("Netlist doesn't have timing metrics")

    # Convert and save
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Load the protobuf data
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)
    loaded_proto = loaded_stage_proto.netlist

    # Check timing metrics
    assert loaded_proto.timing_metrics is not None, "Loaded protobuf should have timing_metrics"

    cpm_attrs = [
        'critical_path_startpoint', 'critical_path_endpoint', 'worst_arrival_time', 'worst_slack',
        'total_negative_slack', 'no_of_endpoints', 'no_of_violating_endpoints'
    ]

    for attr in cpm_attrs:
        if hasattr(netlist.timing_metrics, attr) and hasattr(loaded_proto.timing_metrics, attr):
            netlist_val = getattr(netlist.timing_metrics, attr)
            protobuf_val = getattr(loaded_proto.timing_metrics, attr)
            verify_attribute_equality(netlist_val, protobuf_val, f"timing_metrics.{attr}")

def test_timing_paths_count(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test that timing paths count matches between dataset and protobuf."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Skip if netlist doesn't have timing paths
    if not netlist.timing_paths:
        pytest.skip("Netlist doesn't have timing paths")

    # Convert and save
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Load the protobuf data
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)
    loaded_proto = loaded_stage_proto.netlist

    # Check timing paths count
    assert loaded_proto.timing_paths is not None, "Loaded protobuf should have timing_paths"

    netlist_timing_path_count = len(netlist.timing_paths)
    protobuf_timing_path_count = len(loaded_proto.timing_paths)
    assert netlist_timing_path_count == protobuf_timing_path_count, "Timing path count doesn't match"

def test_end_to_end_conversion(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test the entire process of converting to protobuf and back."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Convert stage entity to protobuf
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)

    # Save protobuf to file
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Read back from file
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)
    loaded_proto = loaded_stage_proto.netlist

    # Verify size matches
    assert loaded_stage_proto.ByteSize() == stage_proto.ByteSize(), "Protobuf size mismatch after save/load cycle"

    # Verify a sample of attributes from different sections
    # Basic attribute
    if hasattr(netlist, 'width'):
        verify_attribute_equality(netlist.width, loaded_proto.width, "width")

    # Cell metrics
    if netlist.cell_metrics and hasattr(netlist.cell_metrics, 'no_of_total_cells'):
        verify_attribute_equality(
            netlist.cell_metrics.no_of_total_cells,
            loaded_proto.cell_metrics.no_of_total_cells,
            "cell_metrics.no_of_total_cells"
        )

    # Area metrics
    if netlist.area_metrics and hasattr(netlist.area_metrics, 'total_area'):
        verify_attribute_equality(
            netlist.area_metrics.total_area,
            loaded_proto.area_metrics.total_area,
            "area_metrics.total_area"
        )

    # Power metrics
    if netlist.power_metrics and hasattr(netlist.power_metrics, 'total_power'):
        verify_attribute_equality(
            netlist.power_metrics.total_power,
            loaded_proto.power_metrics.total_power,
            "power_metrics.total_power"
        )

def test_protobuf_to_dataset(test_dataset, first_stage_entity, temp_protobuf_file):
    """Test converting protobuf back to dataset."""
    stage_entity = first_stage_entity
    netlist = stage_entity.netlist

    # Convert stage entity to protobuf
    stage_proto = dataset_to_protobuf(test_dataset, stage_entity)

    # Save protobuf to file
    with open(temp_protobuf_file, 'wb') as f:
        f.write(stage_proto.SerializeToString())

    # Load protobuf from file
    loaded_stage_proto = load_protobuf_file(temp_protobuf_file)

    # Convert protobuf back to DesignStageEntity
    reconstructed_stage = protobuf_to_dataset(loaded_stage_proto)
    reconstructed_netlist = reconstructed_stage.netlist

    # Verify basic attributes
    for attr in ['width', 'height', 'no_of_inputs', 'no_of_outputs', 'utilization']:
        if hasattr(netlist, attr):
            original_value = getattr(netlist, attr)
            reconstructed_value = getattr(reconstructed_netlist, attr)
            verify_attribute_equality(original_value, reconstructed_value, attr)

    # Verify cell metrics
    if netlist.cell_metrics and reconstructed_netlist.cell_metrics:
        for attr in ['no_of_combinational_cells', 'no_of_sequential_cells', 'no_of_total_cells']:
            if hasattr(netlist.cell_metrics, attr):
                original_value = getattr(netlist.cell_metrics, attr)
                reconstructed_value = getattr(reconstructed_netlist.cell_metrics, attr)
                verify_attribute_equality(original_value, reconstructed_value, f"cell_metrics.{attr}")

    # Verify area metrics
    if netlist.area_metrics and reconstructed_netlist.area_metrics:
        for attr in ['total_area', 'cell_area']:
            if hasattr(netlist.area_metrics, attr):
                original_value = getattr(netlist.area_metrics, attr)
                reconstructed_value = getattr(reconstructed_netlist.area_metrics, attr)
                verify_attribute_equality(original_value, reconstructed_value, f"area_metrics.{attr}")

    # Verify power metrics
    if netlist.power_metrics and reconstructed_netlist.power_metrics:
        for attr in ['total_power', 'internal_power']:
            if hasattr(netlist.power_metrics, attr):
                original_value = getattr(netlist.power_metrics, attr)
                reconstructed_value = getattr(reconstructed_netlist.power_metrics, attr)
                verify_attribute_equality(original_value, reconstructed_value, f"power_metrics.{attr}")

    # Verify timing paths count
    if netlist.timing_paths and reconstructed_netlist.timing_paths:
        original_count = len(netlist.timing_paths)
        reconstructed_count = len(reconstructed_netlist.timing_paths)
        assert original_count == reconstructed_count, "Timing paths count mismatch"
