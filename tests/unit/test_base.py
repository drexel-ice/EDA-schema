# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/unit/test_base.py
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
Tests for BaseEntity and GraphEntity classes.
"""
import pytest
import numpy as np
import networkx as nx

from eda_schema import entity
from eda_schema.base import Image2D


class TestBaseEntity:
    """Test BaseEntity functionality."""

    def test_base_entity_creation(self, sample_netlist_data):
        """Test creating a BaseEntity subclass."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        assert netlist is not None
        assert netlist.flow_id == 'test_flow_001'
        assert netlist.stage == 'floorplan'
        assert netlist.width == 100.0

    def test_base_entity_tabular_data(self, sample_netlist_data):
        """Test extracting tabular data from entity."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        tabular = netlist.get_tabular_data()

        assert isinstance(tabular, dict)
        assert 'flow_id' in tabular
        assert 'stage' in tabular
        assert 'width' in tabular
        assert 'no_of_cells' in tabular

    def test_base_entity_image_data(self, sample_netlist_data):
        """Test extracting image data from entity."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        images = netlist.get_image_data()

        assert isinstance(images, dict)
        # Image fields should be present even if None
        assert 'cell_placement' in images or 'routing' in images

    def test_base_entity_validation_types(self, sample_netlist_data):
        """Test type validation."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        # Should not raise for valid data, including generic types like Dict[str, Image2D]
        netlist.validate_types()
        assert netlist is not None

    def test_base_entity_validation_invalid_type(self, sample_netlist_data):
        """Test validation catches invalid types."""
        # Create entity with invalid type (string instead of int)
        invalid_data = sample_netlist_data.copy()
        invalid_data['no_of_cells'] = "100"  # String instead of int

        # Dataclass will accept it, but validation should catch it
        netlist = entity.NetlistEntity(**invalid_data)
        with pytest.raises(TypeError):
            netlist.validate_types()

    def test_base_entity_repr(self, sample_netlist_data):
        """Test string representation."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        repr_str = repr(netlist)
        assert 'NetlistEntity' in repr_str
        assert 'test_flow_001' in repr_str


class TestGraphEntity:
    """Test GraphEntity functionality."""

    def test_graph_entity_creation(self, sample_netlist_data):
        """Test creating a GraphEntity."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        assert netlist is not None
        assert hasattr(netlist, '_graph')  # pylint: disable=protected-access
        assert isinstance(netlist._graph, nx.DiGraph)  # pylint: disable=protected-access

    def test_graph_entity_nodes_property(self, sample_netlist_data):
        """Test accessing nodes property."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        nodes = netlist.nodes
        assert nodes is not None
        # Initially empty graph
        assert len(list(nodes)) == 0

    def test_graph_entity_edges_property(self, sample_netlist_data):
        """Test accessing edges property."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        edges = netlist.edges
        assert edges is not None
        # Initially empty graph
        assert len(list(edges)) == 0

    def test_graph_entity_add_node(self, sample_netlist_data, sample_gate_data):
        """Test adding a node to the graph."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        gate = entity.GateEntity(**sample_gate_data)
        netlist.add_node(sample_gate_data['name'], type='GATE', entity=gate)

        assert sample_gate_data['name'] in netlist.nodes
        assert netlist.nodes[sample_gate_data['name']]['type'] == 'GATE'
        assert netlist.nodes[sample_gate_data['name']]['entity'] == gate

    def test_graph_entity_add_edge(self, sample_netlist_data):
        """Test adding an edge to the graph."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')

        assert ('node1', 'node2') in netlist.edges

    def test_graph_entity_predecessors(self, sample_netlist_data):
        """Test getting predecessors of a node."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_node('node3', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')
        netlist.add_edge('node3', 'node2')

        preds = list(netlist.predecessors('node2'))
        assert 'node1' in preds
        assert 'node3' in preds
        assert len(preds) == 2

    def test_graph_entity_successors(self, sample_netlist_data):
        """Test getting successors of a node."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_node('node3', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')
        netlist.add_edge('node1', 'node3')

        succs = list(netlist.successors('node1'))
        assert 'node2' in succs
        assert 'node3' in succs
        assert len(succs) == 2

    def test_graph_entity_subgraph(self, sample_netlist_data):
        """Test creating a subgraph."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_node('node3', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')
        netlist.add_edge('node2', 'node3')

        subgraph = netlist.subgraph(['node1', 'node2'])
        assert 'node1' in subgraph.nodes
        assert 'node2' in subgraph.nodes
        assert 'node3' not in subgraph.nodes

    def test_graph_entity_node_validation(self, sample_netlist_data, sample_gate_data):
        """Test node type validation."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Valid node type
        gate = entity.GateEntity(**sample_gate_data)
        netlist.add_node(sample_gate_data['name'], type='GATE', entity=gate)

        # Invalid node type should raise ValueError
        with pytest.raises(ValueError):
            netlist.add_node('invalid', type='INVALID_TYPE', entity=None)

    def test_graph_entity_get_graph_data(self, sample_netlist_data):
        """Test getting graph data representation."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')

        graph_data = netlist.get_graph_data()
        assert 'nodes' in graph_data
        assert 'node_types' in graph_data
        assert 'edges' in graph_data
        assert 'node1' in graph_data['nodes']
        assert ['node1', 'node2'] in graph_data['edges']

    def test_graph_entity_load_graph_data(self, sample_netlist_data):
        """Test loading graph data."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        graph_data = {
            'nodes': ['node1', 'node2'],
            'node_types': ['GATE', 'GATE'],
            'edges': [['node1', 'node2']]
        }

        netlist.load_graph_data(graph_data)

        assert 'node1' in netlist.nodes
        assert 'node2' in netlist.nodes
        assert ('node1', 'node2') in netlist.edges

    def test_graph_entity_remove_node(self, sample_netlist_data):
        """Test removing a node from the graph."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')

        # Remove node (should also remove edges)
        netlist._graph.remove_node('node1')  # pylint: disable=protected-access

        assert 'node1' not in netlist.nodes
        assert 'node2' in netlist.nodes
        assert ('node1', 'node2') not in netlist.edges

    def test_graph_entity_remove_edge(self, sample_netlist_data):
        """Test removing an edge from the graph."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')

        netlist._graph.remove_edge('node1', 'node2')  # pylint: disable=protected-access

        assert ('node1', 'node2') not in netlist.edges
        assert 'node1' in netlist.nodes
        assert 'node2' in netlist.nodes

    def test_graph_entity_degree(self, sample_netlist_data):
        """Test getting node degree."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_node('node3', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')
        netlist.add_edge('node1', 'node3')

        # Out-degree (successors)
        assert netlist._graph.out_degree('node1') == 2  # pylint: disable=protected-access
        assert netlist._graph.out_degree('node2') == 0  # pylint: disable=protected-access

        # In-degree (predecessors)
        assert netlist._graph.in_degree('node2') == 1  # pylint: disable=protected-access
        assert netlist._graph.in_degree('node1') == 0  # pylint: disable=protected-access

    def test_graph_entity_has_node(self, sample_netlist_data):
        """Test checking if node exists."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)

        assert 'node1' in netlist.nodes
        assert 'node2' not in netlist.nodes

    def test_graph_entity_has_edge(self, sample_netlist_data):
        """Test checking if edge exists."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')

        assert ('node1', 'node2') in netlist.edges
        assert ('node2', 'node1') not in netlist.edges


class TestImage2D:
    """Test Image2D functionality."""

    def test_image2d_creation(self):
        """Test creating Image2D."""
        data = np.array([[1, 2], [3, 4]])
        image = Image2D(data)

        assert image.shape == (2, 2)
        assert np.array_equal(image, data)
        assert isinstance(image, Image2D)

    def test_image2d_validation(self):
        """Test Image2D validation."""
        # Valid 2D array
        data = np.array([[1, 2], [3, 4]])
        image = Image2D(data)
        image.validate()  # Should not raise

        # Invalid: 1D array
        data_1d = np.array([1, 2, 3])
        image_1d = Image2D(data_1d)
        with pytest.raises(ValueError, match="must be 2D"):
            image_1d.validate()

        # Invalid: empty array
        data_empty = np.array([[]])
        image_empty = Image2D(data_empty)
        with pytest.raises(ValueError, match="cannot be empty"):
            image_empty.validate()

    def test_image2d_none_handling(self, sample_netlist_data):
        """Test that None Image2D fields are handled correctly."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Image fields should be None by default
        assert netlist.cell_placement is None
        assert netlist.routing is None

        # get_image_data should handle None values
        images = netlist.get_image_data()
        assert isinstance(images, dict)
