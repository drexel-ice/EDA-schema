# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/unit/test_json_utils.py
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

"""
Tests for JSON utilities.
"""
import json
from pathlib import Path
from dataclasses import asdict

import pytest

from eda_schema.serialization.json_utils import load_json, dump_json
from eda_schema import entity
from eda_schema.errors import EDASchemaError


class TestJSONUtils:
    """Test JSON utility functions."""

    def test_dump_json(self, temp_dir, sample_netlist_data):
        """Test dumping entity to JSON."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        json_dir = Path(temp_dir) / "netlistentity"
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / "test.json"

        # Use asdict from dataclasses since json_utils expects it
        data_dict = asdict(netlist)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f)

        assert json_path.exists()
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert 'flow_id' in data
        assert data['flow_id'] == 'test_flow_001'

    def test_load_json(self, temp_dir, sample_netlist_data):
        """Test loading entity from JSON."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        json_path = Path(temp_dir) / "netlistentity.json"

        # Create JSON file manually since load_json expects a specific format
        data_dict = asdict(netlist)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f)

        # Then load it
        loaded = load_json(str(temp_dir), entity.NetlistEntity)
        assert loaded is not None
        assert loaded.flow_id == netlist.flow_id
        assert loaded.stage == netlist.stage

    def test_load_json_filters_internal_fields(self, temp_dir, sample_netlist_data):
        """Test that load_json filters out internal fields starting with _."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        json_path = Path(temp_dir) / "netlistentity.json"

        # Create JSON with internal fields
        data_dict = asdict(netlist)
        data_dict['_internal_field'] = 'should_be_filtered'
        data_dict['_another_internal'] = 123
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f)

        # Should load successfully without internal fields
        loaded = load_json(str(temp_dir), entity.NetlistEntity)
        assert loaded is not None
        assert not hasattr(loaded, '_internal_field')

    def test_load_json_invalid_class(self, temp_dir):
        """Test load_json with invalid class raises error."""
        json_path = Path(temp_dir) / "invalid.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({'test': 'data'}, f)

        with pytest.raises(EDASchemaError, match="schema_class must be a subclass"):
            load_json(str(temp_dir), dict)  # dict is not a BaseEntity subclass

    def test_dump_json_function(self, temp_dir, sample_netlist_data):
        """Test dump_json function."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        json_dir = Path(temp_dir) / "netlistentity"
        json_dir.mkdir(parents=True, exist_ok=True)

        dump_json(str(temp_dir), netlist, "test")

        json_path = json_dir / "test.json"
        assert json_path.exists()
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert 'flow_id' in data
        assert data['flow_id'] == netlist.flow_id

    def test_dump_json_invalid_object(self, temp_dir):
        """Test dump_json with invalid object raises error."""
        with pytest.raises(EDASchemaError, match="schema_object must be an instance"):
            dump_json(str(temp_dir), "not_an_entity", "test")

    def test_load_json_file_not_found(self, temp_dir):
        """Test load_json with non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_json(str(temp_dir), entity.NetlistEntity)
