"""Shared fixtures and helpers for data tests."""
import pytest
from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB

DATASET_DIR = "dataset/test"
FLOW_ID = 'gcd-000001'
PHASES = ["floorplan", "global_place", "place_resized", "detailed_place",
          "cts", "global_route", "detailed_route", "final"]


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


def get_design_stage(dataset, phase):
    """Helper function to get design stage for a phase."""
    flow = dataset[FLOW_ID]
    return flow.stages[phase]
