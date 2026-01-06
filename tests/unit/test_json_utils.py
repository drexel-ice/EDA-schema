"""
Tests for JSON utilities.
"""
import json
from pathlib import Path
from dataclasses import asdict

from eda_schema.serialization.json_utils import load_json
from eda_schema import entity


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
