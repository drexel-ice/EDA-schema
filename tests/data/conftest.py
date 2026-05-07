# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/data/conftest.py
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
