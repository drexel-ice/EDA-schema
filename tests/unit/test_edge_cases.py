# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/unit/test_edge_cases.py
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
Edge case tests for eda_schema library.
"""
import pytest
from eda_schema import entity


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_entity_with_none_values(self, sample_netlist_data):
        """Test entity creation with None values for optional fields."""
        data = sample_netlist_data.copy()
        data['width'] = None
        data['height'] = None

        netlist = entity.NetlistEntity(**data)
        assert netlist.width is None
        assert netlist.height is None

    def test_entity_with_zero_values(self, sample_netlist_data):
        """Test entity creation with zero values."""
        data = sample_netlist_data.copy()
        data['no_of_cells'] = 0
        data['no_of_nets'] = 0

        netlist = entity.NetlistEntity(**data)
        assert netlist.no_of_cells == 0
        assert netlist.no_of_nets == 0

    def test_entity_with_empty_string(self, sample_gate_data):
        """Test entity creation with empty string."""
        data = sample_gate_data.copy()
        data['name'] = ''

        gate = entity.GateEntity(**data)
        assert gate.name == ''

    def test_graph_entity_empty_graph(self, sample_netlist_data):
        """Test graph entity with no nodes or edges."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        assert len(list(netlist.nodes)) == 0
        assert len(list(netlist.edges)) == 0

    def test_graph_entity_single_node(self, sample_netlist_data):
        """Test graph entity with single node."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        netlist.add_node('node1', type='GATE', entity=None)

        assert len(list(netlist.nodes)) == 1
        assert len(list(netlist.edges)) == 0

    def test_entity_with_negative_values(self, sample_power_metrics_data):  # pylint: disable=unused-argument
        """Test entity with negative values (e.g., negative slack)."""
        # Timing metrics can have negative slack
        timing = entity.TimingMetricsEntity(
            flow_id='test_flow_001',
            stage='floorplan',
            total_negative_slack=-10.5,
            worst_slack=-5.2,
            critical_path_startpoint='start',
            critical_path_endpoint='end',
            worst_arrival_time=100.0,
            worst_required_time=95.0,
            no_of_endpoints=50,
            no_of_violating_endpoints=5
        )
        assert timing.total_negative_slack == -10.5
        assert timing.worst_slack == -5.2

    def test_entity_with_very_large_values(self, sample_netlist_data):
        """Test entity with very large numeric values."""
        data = sample_netlist_data.copy()
        data['no_of_cells'] = 1000000
        data['no_of_nets'] = 2000000

        netlist = entity.NetlistEntity(**data)
        assert netlist.no_of_cells == 1000000
        assert netlist.no_of_nets == 2000000

    def test_entity_with_very_small_values(self, sample_power_metrics_data):
        """Test entity with very small float values."""
        data = sample_power_metrics_data.copy()
        data['leakage_power'] = 1e-10
        data['switching_power'] = 1e-8

        power = entity.PowerMetricsEntity(**data)
        assert power.leakage_power == 1e-10
        assert power.switching_power == 1e-8

    def test_graph_entity_self_loop(self, sample_netlist_data):
        """Test graph entity with self-loop edge."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_edge('node1', 'node1')  # Self-loop

        assert ('node1', 'node1') in netlist.edges

    def test_graph_entity_multiple_edges_same_nodes(self, sample_netlist_data):
        """Test graph entity with multiple edges between same nodes (not allowed in DiGraph)."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')
        # Adding same edge again should not create duplicate
        netlist.add_edge('node1', 'node2')

        # DiGraph doesn't allow duplicate edges
        edges = list(netlist.edges)
        assert edges.count(('node1', 'node2')) == 1

    def test_entity_with_unicode_strings(self, sample_gate_data):
        """Test entity with unicode characters in strings."""
        data = sample_gate_data.copy()
        data['name'] = 'gate_测试_001'
        data['standard_cell'] = 'NAND2_αβγ'

        gate = entity.GateEntity(**data)
        assert gate.name == 'gate_测试_001'
        assert gate.standard_cell == 'NAND2_αβγ'

    def test_entity_with_special_characters(self, sample_net_data):
        """Test entity with special characters in names."""
        data = sample_net_data.copy()
        data['name'] = 'net_001_$%^&*()'

        net = entity.NetEntity(**data)
        assert net.name == 'net_001_$%^&*()'

    def test_graph_entity_isolated_nodes(self, sample_netlist_data):
        """Test graph entity with isolated nodes (no edges)."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_node('node3', type='GATE', entity=None)
        # No edges added

        assert len(list(netlist.nodes)) == 3
        assert len(list(netlist.edges)) == 0
        # All nodes should have degree 0
        assert netlist._graph.degree('node1') == 0  # pylint: disable=protected-access

    def test_entity_optional_fields_all_none(self, sample_gate_data):
        """Test entity with all optional fields set to None."""
        data = sample_gate_data.copy()
        data['x_min'] = None
        data['y_min'] = None
        data['x_max'] = None
        data['y_max'] = None

        gate = entity.GateEntity(**data)
        assert gate.x_min is None
        assert gate.y_min is None
        assert gate.x_max is None
        assert gate.y_max is None

    def test_graph_entity_large_graph(self, sample_netlist_data):
        """Test graph entity with many nodes and edges."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Add 100 nodes
        for i in range(100):
            netlist.add_node(f'node_{i}', type='GATE', entity=None)

        # Add edges in a chain
        for i in range(99):
            netlist.add_edge(f'node_{i}', f'node_{i+1}')

        assert len(list(netlist.nodes)) == 100
        assert len(list(netlist.edges)) == 99

    def test_entity_validation_with_invalid_type(self, sample_netlist_data):
        """Test that validation catches type errors."""
        # Create entity with wrong type (will be caught by validation)
        invalid_data = sample_netlist_data.copy()
        invalid_data['no_of_cells'] = "not_an_int"  # String instead of int

        # Dataclass will accept it, but validation should catch it
        netlist = entity.NetlistEntity(**invalid_data)
        with pytest.raises(TypeError):
            netlist.validate_types()
