# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/utils/test_netlist_diff.py
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

import pytest
from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB
from eda_schema.utils.netlist_diff import compare_netlists_by_cells, compare_netlists_by_nets

DATASET_DIR = "dataset/test"
FLOW_ID = 'gcd-000001'


@pytest.fixture(scope="module")
def dataset():
    """Load dataset once per test module."""
    dataset = Dataset(ParquetDB(DATASET_DIR))
    dataset.load(flow_id=FLOW_ID)
    return dataset


@pytest.mark.parametrize(
    "phase1, phase2, expected_result",
    [
        #### TESTING CELL DIFFERENCES BETWEEN ADJACENT PHASES

        # No change
        ("floorplan", "global_place", {
            'init_stage_count': 213,
            'final_stage_count': 213,
            'names_match': 213,
            'names_match_stdcell_match': 213,
            'names_match_stdcell_not_match': 0,
            'names_match_stdcell_not_match_resized': 0,
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 0,
            'names_not_match_clone': 0,
            'names_not_match_buffered': 0,
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0
        }),
        # Resizing and buffer insertion
        ("global_place", "place_resized", {
            'init_stage_count': 213,
            'final_stage_count': 266,
            'names_match': 213,
            'names_match_stdcell_match': 160,
            'names_match_stdcell_not_match': 53,
            'names_match_stdcell_not_match_resized': 53, # [INFO RSZ-0039] Resized 51 instances.
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 53,
            'names_not_match_clone': 0,
            'names_not_match_buffered': 53, # [INFO RSZ-0027] Inserted 35 input buffers. [INFO RSZ-0028] Inserted 18 output buffers.
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0,
        }),
        # No change
        ("place_resized", "detailed_place", {
            'init_stage_count': 266,
            'final_stage_count': 266,
            'names_match': 266,
            'names_match_stdcell_match': 266,
            'names_match_stdcell_not_match': 0,
            'names_match_stdcell_not_match_resized': 0,
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 0,
            'names_not_match_clone': 0,
            'names_not_match_buffered': 0,
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0
        }),
        # Resizing, buffer insertion, and clone insertion
        ("detailed_place", "cts", {
            'init_stage_count': 266,
            'final_stage_count': 340,
            'names_match': 266,
            'names_match_stdcell_match': 259,
            'names_match_stdcell_not_match': 7,
            'names_match_stdcell_not_match_resized': 7, # [INFO RSZ-0041] Resized 10 instances.
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 74,
            'names_not_match_clone': 1, # [INFO RSZ-0049] Cloned 1 instances.
            'names_not_match_buffered': 73, # [INFO CTS-0018] Created 5 clock buffers. [INFO RSZ-0040] Inserted 32 buffers. [INFO RSZ-0032] Inserted 36 hold buffers.
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0
        }),
        # Resizing and buffer insertion
        ("cts", "global_route", {
            'init_stage_count': 340,
            'final_stage_count': 354,
            'names_match': 340,
            'names_match_stdcell_match': 254,
            'names_match_stdcell_not_match': 86,
            'names_match_stdcell_not_match_resized': 86, # [INFO RSZ-0039] Resized 77 instances. [INFO RSZ-0041] Resized 25 instances.
            'names_match_stdcell_not_match_delay': 65,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 14,
            'names_not_match_clone': 0,
            'names_not_match_buffered': 14, # [INFO RSZ-0040] Inserted 1 buffers. [INFO RSZ-0032] Inserted 13 hold buffers.
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0
        }),
        # No change
        ("global_route", "detailed_route", {
            'init_stage_count': 354,
            'final_stage_count': 354,
            'names_match': 354,
            'names_match_stdcell_match': 354,
            'names_match_stdcell_not_match': 0,
            'names_match_stdcell_not_match_resized': 0,
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 0,
            'names_not_match_clone': 0,
            'names_not_match_buffered': 0,
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0,
        }),


        #### TESTING CELL DIFFERENCES BETWEEN INITIAL AND CURRENT PHASES

        ("floorplan", "place_resized", {
            'init_stage_count': 213,
            'final_stage_count': 266,
            'names_match': 213,
            'names_match_stdcell_match': 160,
            'names_match_stdcell_not_match': 53,
            'names_match_stdcell_not_match_resized': 53, # [INFO RSZ-0039] Resized 51 instances.
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 53,
            'names_not_match_clone': 0,
            'names_not_match_buffered': 53, # [INFO RSZ-0027] Inserted 35 input buffers. [INFO RSZ-0028] Inserted 18 output buffers.
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0,
        }),
        ("floorplan", "detailed_place", {
            'init_stage_count': 213,
            'final_stage_count': 266,
            'names_match': 213,
            'names_match_stdcell_match': 160,
            'names_match_stdcell_not_match': 53,
            'names_match_stdcell_not_match_resized': 53, # [INFO RSZ-0039] Resized 51 instances.
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 53,
            'names_not_match_clone': 0,
            'names_not_match_buffered': 53, # [INFO RSZ-0027] Inserted 35 input buffers. [INFO RSZ-0028] Inserted 18 output buffers.
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0,
        }),
        ("floorplan", "cts", {
            'init_stage_count': 213,
            'final_stage_count': 340,
            'names_match': 213,
            'names_match_stdcell_match': 153,
            'names_match_stdcell_not_match': 60,
            'names_match_stdcell_not_match_resized': 60, # [INFO RSZ-0039] Resized 51 instances. [INFO RSZ-0041] Resized 10 instances.
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 127,
            'names_not_match_clone': 1, # [INFO RSZ-0049] Cloned 1 instances.
            'names_not_match_buffered': 126, # [INFO RSZ-0027] Inserted 35 input buffers. [INFO RSZ-0028] Inserted 18 output buffers. [INFO CTS-0018] Created 5 clock buffers. [INFO RSZ-0040] Inserted 32 buffers. [INFO RSZ-0032] Inserted 36 hold buffers.
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0,
        }),
        ("floorplan", "global_route", {
            'init_stage_count': 213,
            'final_stage_count': 354,
            'names_match': 213,
            'names_match_stdcell_match': 152,
            'names_match_stdcell_not_match': 61,
            'names_match_stdcell_not_match_resized': 61, # [INFO RSZ-0039] Resized 51 instances. [INFO RSZ-0041] Resized 10 instances. [INFO RSZ-0039] Resized 77 instances. [INFO RSZ-0041] Resized 25 instances.
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 141,
            'names_not_match_clone': 1, # [INFO RSZ-0049] Cloned 1 instances.
            'names_not_match_buffered': 140, # [INFO RSZ-0027] Inserted 35 input buffers. [INFO RSZ-0028] Inserted 18 output buffers. [INFO CTS-0018] Created 5 clock buffers. [INFO RSZ-0040] Inserted 32 buffers. [INFO RSZ-0032] Inserted 36 hold buffers. [INFO RSZ-0040] Inserted 1 buffers. [INFO RSZ-0032] Inserted 13 hold buffers.
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0,
        }),
        ("floorplan", "detailed_route", {
            'init_stage_count': 213,
            'final_stage_count': 354,
            'names_match': 213,
            'names_match_stdcell_match': 152,
            'names_match_stdcell_not_match': 61,
            'names_match_stdcell_not_match_resized': 61, # [INFO RSZ-0039] Resized 51 instances. [INFO RSZ-0041] Resized 10 instances. [INFO RSZ-0039] Resized 77 instances. [INFO RSZ-0041] Resized 25 instances.
            'names_match_stdcell_not_match_delay': 0,
            'names_match_stdcell_not_match_remaining': 0,
            'names_not_match': 141,
            'names_not_match_clone': 1, # [INFO RSZ-0049] Cloned 1 instances.
            'names_not_match_buffered': 140, # [INFO RSZ-0027] Inserted 35 input buffers. [INFO RSZ-0028] Inserted 18 output buffers. [INFO CTS-0018] Created 5 clock buffers. [INFO RSZ-0040] Inserted 32 buffers. [INFO RSZ-0032] Inserted 36 hold buffers. [INFO RSZ-0040] Inserted 1 buffers. [INFO RSZ-0032] Inserted 13 hold buffers.
            'names_not_match_constant_logic': 0,
            'names_not_match_remaining': 0,
            'removed_cell': 0,
            'removed_cell_is_constant_logic': 0,
        }),
    ]
)
def test_compare_netlists_by_cells(dataset, phase1, phase2, expected_result):
    flow = dataset[FLOW_ID]
    netlist1 = flow.stages[phase1].netlist
    netlist2 = flow.stages[phase2].netlist
    _, _, result = compare_netlists_by_cells(netlist1, netlist2)

    assert result == expected_result


@pytest.mark.parametrize(
    "phase1, phase2, expected_result",
    [
        ("floorplan", "global_place", {
            'init_stage_count': 272,
            'final_stage_count': 272,
            'names_match': 272,
            'names_match_neighbors_match': 272,
            'names_match_neighbors_not_match': 0,
            'names_match_neighbors_not_match_resized': 0,
            'names_match_neighbors_not_match_delay': 0,
            'names_match_neighbors_not_match_buffered': 0,
            'names_match_neighbors_not_match_remaining': 0,
            'names_not_match': 0,
            'names_not_match_buffer_added': 0,
            'names_not_match_buffer_added_output': 0,
            'names_not_match_conb': 0,
            'names_not_match_remaining': 0,
            'removed_net': 0
        }),
        ("global_place", "place_resized", {
            'init_stage_count': 272,
            'final_stage_count': 325,
            'names_match': 272,
            'names_match_neighbors_match': 219,
            'names_match_neighbors_not_match': 53,
            'names_match_neighbors_not_match_resized': 0,
            'names_match_neighbors_not_match_delay': 0,
            'names_match_neighbors_not_match_buffered': 35,
            'names_match_neighbors_not_match_remaining': 18,
            'names_not_match': 53,
            'names_not_match_buffer_added': 35, # [INFO RSZ-0027] Inserted 35 input buffers.
            'names_not_match_buffer_added_output': 0,
            'names_not_match_conb': 0,
            'names_not_match_remaining': 18,
            'removed_net': 0,
        }),
        ("place_resized", "detailed_place", {
            'init_stage_count': 325,
            'final_stage_count': 325,
            'names_match': 325,
            'names_match_neighbors_match': 325,
            'names_match_neighbors_not_match': 0,
            'names_match_neighbors_not_match_resized': 0,
            'names_match_neighbors_not_match_delay': 0,
            'names_match_neighbors_not_match_buffered': 0,
            'names_match_neighbors_not_match_remaining': 0,
            'names_not_match': 0,
            'names_not_match_buffer_added': 0,
            'names_not_match_buffer_added_output': 0,
            'names_not_match_conb': 0,
            'names_not_match_remaining': 0,
            'removed_net': 0
        }),
    ]
)
def test_compare_netlists_by_nets(dataset, phase1, phase2, expected_result):
    flow = dataset[FLOW_ID]
    netlist1 = flow.stages[phase1].netlist
    netlist2 = flow.stages[phase2].netlist
    _, _, result = compare_netlists_by_nets(netlist1, netlist2)

    assert result == expected_result
