"""
Shared pytest fixtures for the EDA schema test suite.

This module provides reusable fixtures for all test files.
"""
import pytest
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB, FileDB


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test data."""
    return str(tmp_path)


@pytest.fixture
def sample_netlist_data():
    """Sample data for NetlistEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'no_of_inputs': 10,
        'no_of_outputs': 5,
        'no_of_cells': 100,
        'no_of_nets': 150,
        'no_of_pins': 200,
        'utilization': 0.75,
        'width': 100.0,
        'height': 100.0,
    }


@pytest.fixture
def sample_gate_data():
    """Sample data for GateEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'name': 'gate_001',
        'standard_cell': 'NAND2_X1',
        'x_min': 10.0,
        'y_min': 20.0,
        'x_max': 15.0,
        'y_max': 25.0,
        'no_of_inputs': 2,
        'no_of_outputs': 1,
    }


@pytest.fixture
def sample_port_data():
    """Sample data for PortEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'name': 'port_001',
        'direction': 'INPUT',
        'x': 0.0,
        'y': 0.0,
    }


@pytest.fixture
def sample_net_data():
    """Sample data for NetEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'name': 'net_001',
        'is_special_net': False,
        'no_of_fanouts': 3,
        'x_min': 0.0,
        'y_min': 0.0,
        'x_max': 100.0,
        'y_max': 100.0,
        'length': 150.0,
    }


@pytest.fixture
def sample_power_metrics_data():
    """Sample data for PowerMetricsEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'combinational_power': 0.1,
        'sequential_power': 0.2,
        'macro_power': 0.05,
        'internal_power': 0.08,
        'switching_power': 0.07,
        'leakage_power': 0.01,
        'total_power': 0.51,
    }


@pytest.fixture
def sample_area_metrics_data():
    """Sample data for AreaMetricsEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'combinational_cell_area': 100.0,
        'sequential_cell_area': 50.0,
        'buffer_area': 10.0,
        'inverter_area': 5.0,
        'filler_area': 0.0,
        'tap_cell_area': 0.0,
        'diode_area': 0.0,
        'macro_area': 0.0,
        'cell_area': 165.0,
        'total_area': 200.0,
    }


@pytest.fixture
def sample_cell_metrics_data():
    """Sample data for CellMetricsEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'no_of_combinational_cells': 80,
        'no_of_sequential_cells': 20,
        'no_of_buffers': 3,
        'no_of_inverters': 2,
        'no_of_fillers': 0,
        'no_of_tap_cells': 0,
        'no_of_diodes': 0,
        'no_of_macros': 0,
        'no_of_total_cells': 100,
    }


@pytest.fixture
def sample_standard_cell_data():
    """Sample data for StandardCellEntity."""
    return {
        'name': 'NAND2_X1',
        'width': 0.5,
        'height': 2.0,
        'no_of_input_pins': 2,
        'no_of_output_pins': 1,
        'is_sequential': False,
        'is_inverter': False,
        'is_buffer': False,
        'is_filler': False,
        'is_diode': False,
    }


@pytest.fixture
def sample_dataset(temp_dir):
    """Sample Dataset instance."""
    db_path = Path(temp_dir) / "sample_db"
    db = ParquetDB(str(db_path))
    db.create_dataset_tables()
    dataset = Dataset(db)
    return dataset


@pytest.fixture
def sample_file_db(temp_dir):
    """Sample FileDB instance."""
    db_path = Path(temp_dir) / "sample_file_db"
    return FileDB(str(db_path))


@pytest.fixture
def empty_parquet_db(temp_dir):
    """Create an empty ParquetDB with tables already created."""
    db_path = Path(temp_dir) / "empty_db"
    db = ParquetDB(str(db_path))
    db.create_dataset_tables()
    return db


@pytest.fixture
def empty_filedb(temp_dir):
    """Create an empty FileDB with tables already created."""
    db_path = Path(temp_dir) / "empty_filedb"
    db = FileDB(str(db_path))
    db.create_dataset_tables()
    return db


@pytest.fixture
def sample_pin_data():
    """Sample data for PinEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'name': 'pin_001',
        'direction': 'INPUT',
        'is_startpoint': True,
        'is_endpoint': False,
        'x_min': 5.0,
        'y_min': 10.0,
        'x_max': 10.0,
        'y_max': 15.0,
    }


@pytest.fixture
def sample_timing_metrics_data():
    """Sample data for TimingMetricsEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'total_negative_slack': -10.5,
        'worst_slack': -5.2,
        'critical_path_startpoint': 'start_001',
        'critical_path_endpoint': 'end_001',
        'worst_arrival_time': 100.5,
        'worst_required_time': 95.3,
        'no_of_endpoints': 50,
        'no_of_violating_endpoints': 5,
    }


@pytest.fixture
def sample_routability_metrics_data():
    """Sample data for RoutabilityMetricsEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'rudy_net': None,
        'rudy_net_long': None,
        'rudy_net_short': None,
        'rudy_pin': None,
    }


@pytest.fixture
def sample_net_arc_data():
    """Sample data for NetArcEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'startpoint': 'start_001',
        'endpoint': 'end_001',
        'path_type': 'setup',
        'net_name': 'net_001',
        'delay': 1.5,
        'arrival_time': 10.0,
        'slew': 0.5,
        'capacitance': 0.01,
    }


@pytest.fixture
def sample_cell_arc_data():
    """Sample data for CellArcEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'startpoint': 'start_001',
        'endpoint': 'end_001',
        'path_type': 'setup',
        'gate_name': 'gate_001',
        'delay': 2.0,
        'arrival_time': 12.0,
        'slew': 0.6,
    }


@pytest.fixture
def sample_pdn_data():
    """Sample data for PDNEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'routing_vdd': None,
        'routing_vss': None,
        'ir_drop_vdd': None,
        'ir_drop_vss': None,
        'em_vdd': None,
        'em_vss': None,
    }


@pytest.fixture
def sample_clock_tree_data():
    """Sample data for ClockTreeEntity."""
    return {
        'flow_id': 'test_flow_001',
        'stage': 'floorplan',
        'clock_source': 'clk',
        'no_of_buffers': 10,
        'no_of_clock_sinks': 100,
    }
