# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/integration/test_integration.py
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
Integration tests for eda_schema library.
Tests complete workflows and multi-component interactions.
"""
from pathlib import Path

import pytest
import numpy as np

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB
from eda_schema.db.parquet import _load_arrow_table
from eda_schema import entity
from eda_schema.base import Image2D
from eda_schema.errors import DataNotFoundError


class TestIntegration:
    """Basic integration tests combining multiple components."""

    def test_create_netlist_with_graph(self, temp_dir, sample_netlist_data,
                                       sample_gate_data, sample_port_data):
        """Test creating a complete netlist with graph structure."""
        # Create netlist
        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Add gates
        gate1 = entity.GateEntity(**sample_gate_data)
        gate2_data = sample_gate_data.copy()
        gate2_data['name'] = 'gate_002'
        gate2 = entity.GateEntity(**gate2_data)

        netlist.add_node(sample_gate_data['name'], type='GATE', entity=gate1)
        netlist.add_node('gate_002', type='GATE', entity=gate2)

        # Add ports
        port = entity.PortEntity(**sample_port_data)
        netlist.add_node(sample_port_data['name'], type='PORT', entity=port)

        # Add edges
        netlist.add_edge(sample_port_data['name'], sample_gate_data['name'])
        netlist.add_edge(sample_gate_data['name'], 'gate_002')

        # Verify structure
        assert len(list(netlist.nodes)) == 3
        assert len(list(netlist.edges)) == 2
        assert sample_gate_data['name'] in netlist.nodes
        assert (sample_port_data['name'], sample_gate_data['name']) in netlist.edges

    def test_dataset_with_multiple_entities(self, temp_dir, sample_netlist_data,
                                           sample_power_metrics_data,
                                           sample_area_metrics_data):
        """Test Dataset with multiple entity types."""
        db_path = Path(temp_dir) / "integration_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        # Add netlist (graph entity - needs both table and graph data)
        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=sample_netlist_data['flow_id'],
                         stage=sample_netlist_data['stage'])

        # Add power metrics (tabular entity only)
        power = entity.PowerMetricsEntity(**sample_power_metrics_data)
        db.add_table_row('power_metrics', power.get_tabular_data())

        # Add area metrics (tabular entity only)
        area = entity.AreaMetricsEntity(**sample_area_metrics_data)
        db.add_table_row('area_metrics', area.get_tabular_data())

        # Writers are auto-closed before reading
        # Retrieve entities
        retrieved_netlist = db.get_entity('netlists',
                                         flow_id='test_flow_001',
                                         stage='floorplan')
        retrieved_power = db.get_entity('power_metrics',
                                       flow_id='test_flow_001',
                                       stage='floorplan')
        retrieved_area = db.get_entity('area_metrics',
                                      flow_id='test_flow_001',
                                      stage='floorplan')

        assert retrieved_netlist is not None
        assert retrieved_power is not None
        assert retrieved_area is not None

    def test_standard_cells_integration(self, temp_dir):
        """Test standard cells integration with dataset."""
        db_path = Path(temp_dir) / "std_cell_db"
        db = ParquetDB(str(db_path))
        dataset = Dataset(db)

        # Add standard cells
        nand_cell = entity.StandardCellEntity(
            name='NAND2_X1',
            is_sequential=False,
            is_buffer=False,
            is_inverter=False,
            is_filler=False,
            is_diode=False,
            width=0.5,
            height=2.0,
            no_of_input_pins=2,
            no_of_output_pins=1
        )

        dff_cell = entity.StandardCellEntity(
            name='DFF_X1',
            is_sequential=True,
            is_buffer=False,
            is_inverter=False,
            is_filler=False,
            is_diode=False,
            width=1.0,
            height=4.0,
            no_of_input_pins=1,
            no_of_output_pins=1
        )

        dataset.standard_cells.add_cell(nand_cell)
        dataset.standard_cells.add_cell(dff_cell)

        assert 'NAND2_X1' in dataset.standard_cells
        assert 'DFF_X1' in dataset.standard_cells
        assert 'DFF_X1' in dataset.standard_cells.seq_cells
        assert 'NAND2_X1' not in dataset.standard_cells.seq_cells

    def test_graph_traversal(self, temp_dir, sample_netlist_data):
        """Test graph traversal methods."""
        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Create a simple graph: A -> B -> C
        netlist.add_node('A', type='GATE', entity=None)
        netlist.add_node('B', type='GATE', entity=None)
        netlist.add_node('C', type='GATE', entity=None)
        netlist.add_edge('A', 'B')
        netlist.add_edge('B', 'C')

        # Test BFS traversal
        bfs_result = netlist.bfs_traverse('A', fanin=False, fanout=True)
        assert 'B' in bfs_result
        assert 'C' in bfs_result

        # Test DFS traversal
        dfs_result = netlist.dfs_traverse('A', fanin=False, fanout=True)
        assert 'B' in dfs_result
        assert 'C' in dfs_result

    def test_multiple_stages(self, temp_dir, sample_netlist_data):
        """Test handling multiple design stages."""
        db_path = Path(temp_dir) / "multi_stage_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        stages = ['floorplan', 'global_place', 'detailed_place']

        for stage in stages:
            data = sample_netlist_data.copy()
            data['stage'] = stage
            netlist = entity.NetlistEntity(**data)
            db.add_table_row('netlists', netlist.get_tabular_data())
            # Add graph data for each stage
            graph_data = netlist.get_graph_data()
            db.add_graph_data('netlists', graph_data,
                             flow_id=data['flow_id'],
                             stage=stage)

        # Writers are auto-closed before reading
        # Retrieve all stages
        for stage in stages:
            retrieved = db.get_entity('netlists',
                                     flow_id='test_flow_001',
                                     stage=stage)
            assert retrieved.stage == stage


class TestMultiEntityWorkflow:
    """Test workflows involving multiple entity types."""

    def test_complete_design_flow(self, temp_dir, sample_netlist_data,
                                  sample_power_metrics_data,
                                  sample_area_metrics_data):
        """Test complete workflow with all entity types."""
        db_path = Path(temp_dir) / "complete_flow_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        # Add netlist
        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Add power metrics
        power = entity.PowerMetricsEntity(**sample_power_metrics_data)
        db.add_table_row('power_metrics', power.get_tabular_data())

        # Add area metrics
        area = entity.AreaMetricsEntity(**sample_area_metrics_data)
        db.add_table_row('area_metrics', area.get_tabular_data())

        # Retrieve all
        retrieved_netlist = db.get_entity('netlists',
                                         flow_id=netlist.flow_id,
                                         stage=netlist.stage)
        retrieved_power = db.get_entity('power_metrics',
                                       flow_id=power.flow_id,
                                       stage=power.stage)
        retrieved_area = db.get_entity('area_metrics',
                                      flow_id=area.flow_id,
                                      stage=area.stage)

        assert retrieved_netlist.flow_id == netlist.flow_id
        assert retrieved_power.total_power == power.total_power
        assert retrieved_area.total_area == area.total_area

    def test_multi_stage_workflow(self, temp_dir, sample_netlist_data):
        """Test workflow across multiple design stages."""
        db_path = Path(temp_dir) / "multi_stage_workflow_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        stages = ['floorplan', 'global_place', 'detailed_place', 'cts', 'final']

        # Add data for each stage
        for stage in stages:
            data = sample_netlist_data.copy()
            data['stage'] = stage
            data['no_of_cells'] = 100 + len(stage)  # Vary data slightly
            netlist = entity.NetlistEntity(**data)
            db.add_table_row('netlists', netlist.get_tabular_data())
            graph_data = netlist.get_graph_data()
            db.add_graph_data('netlists', graph_data,
                             flow_id=netlist.flow_id, stage=stage)

        # Retrieve all stages for the flow
        df = db.get_table_data('netlists', flow_id=sample_netlist_data['flow_id'])
        assert len(df) == len(stages)
        assert set(df['stage']) == set(stages)

        # Retrieve specific stage
        retrieved = db.get_entity('netlists',
                                 flow_id=sample_netlist_data['flow_id'],
                                 stage='cts')
        assert retrieved.stage == 'cts'

    def test_graph_with_nodes_and_edges(self, temp_dir, sample_netlist_data):
        """Test graph entity with actual nodes and edges."""
        db_path = Path(temp_dir) / "graph_nodes_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Add some nodes and edges to the graph
        netlist.add_node('gate1', type='GATE', name='gate1')
        netlist.add_node('port1', type='PORT', name='port1')
        netlist.add_edge('port1', 'gate1')

        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Retrieve and verify graph structure
        retrieved = db.get_entity('netlists',
                                 flow_id=netlist.flow_id,
                                 stage=netlist.stage)
        assert 'gate1' in retrieved.nodes
        assert 'port1' in retrieved.nodes
        assert ('port1', 'gate1') in retrieved.edges


class TestImageWorkflow:
    """Test workflows involving images."""

    def test_entity_with_images(self, temp_dir, sample_netlist_data):
        """Test storing and retrieving entity with images."""
        db_path = Path(temp_dir) / "image_workflow_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Create and add images
        cell_placement = Image2D(np.random.rand(100, 100))
        routing = Image2D(np.random.rand(100, 100))

        netlist.cell_placement = cell_placement
        netlist.routing = routing

        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Add images using add_entity_images
        db.add_entity_images('netlists', netlist)

        # Retrieve entity
        retrieved = db.get_entity('netlists',
                                 flow_id=netlist.flow_id,
                                 stage=netlist.stage)

        # Images should be loaded
        assert retrieved.cell_placement is not None
        assert retrieved.routing is not None
        assert np.array_equal(cell_placement, retrieved.cell_placement)
        assert np.array_equal(routing, retrieved.routing)

    def test_entity_with_routing_by_metal(self, temp_dir, sample_netlist_data):
        """Test storing and retrieving entity with routing_by_metal dictionary images."""
        db_path = Path(temp_dir) / "routing_by_metal_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Create routing_by_metal dictionary with multiple metal layers
        routing_met1 = Image2D(np.random.rand(50, 50))
        routing_met2 = Image2D(np.random.rand(50, 50))
        routing_met3 = Image2D(np.random.rand(50, 50))

        netlist.routing_by_metal = {
            'met1': routing_met1,
            'met2': routing_met2,
            'met3': routing_met3,
        }

        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Add images using add_entity_images (should handle routing_by_metal)
        db.add_entity_images('netlists', netlist)
        db.close()

        # Retrieve entity
        retrieved = db.get_entity('netlists',
                                 flow_id=netlist.flow_id,
                                 stage=netlist.stage)

        # routing_by_metal should be loaded as a dictionary
        assert retrieved.routing_by_metal is not None
        assert isinstance(retrieved.routing_by_metal, dict)
        assert len(retrieved.routing_by_metal) == 3

        # Verify all metal layers are present
        assert 'met1' in retrieved.routing_by_metal
        assert 'met2' in retrieved.routing_by_metal
        assert 'met3' in retrieved.routing_by_metal

        # Verify images match
        assert np.array_equal(routing_met1, retrieved.routing_by_metal['met1'])
        assert np.array_equal(routing_met2, retrieved.routing_by_metal['met2'])
        assert np.array_equal(routing_met3, retrieved.routing_by_metal['met3'])

        # Verify images are Image2D instances
        assert isinstance(retrieved.routing_by_metal['met1'], Image2D)
        assert isinstance(retrieved.routing_by_metal['met2'], Image2D)
        assert isinstance(retrieved.routing_by_metal['met3'], Image2D)

    def test_clock_tree_with_routing_by_metal(self, temp_dir, sample_netlist_data):
        """Test storing and retrieving ClockTreeEntity with routing_by_metal dictionary images."""
        db_path = Path(temp_dir) / "clock_tree_routing_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Create clock tree with routing_by_metal
        clock_tree = entity.ClockTreeEntity(
            flow_id=netlist.flow_id,
            stage=netlist.stage,
            clock_source='clk',
        )

        # Create routing_by_metal dictionary
        routing_met1 = Image2D(np.random.rand(40, 40))
        routing_met2 = Image2D(np.random.rand(40, 40))

        clock_tree.routing_by_metal = {
            'met1': routing_met1,
            'met2': routing_met2,
        }

        # Add clock tree to netlist
        netlist.clock_trees['clk'] = clock_tree

        # Save clock tree
        db.add_table_row('clock_trees', clock_tree.get_tabular_data())
        clock_graph_data = clock_tree.get_graph_data()
        db.add_graph_data('clock_trees', clock_graph_data,
                         flow_id=clock_tree.flow_id,
                         stage=clock_tree.stage,
                         clock_source=clock_tree.clock_source)
        db.add_entity_images('clock_trees', clock_tree)
        db.close()

        # Retrieve clock tree directly
        retrieved_clock_tree = db.get_entity('clock_trees',
                                            flow_id=clock_tree.flow_id,
                                            stage=clock_tree.stage,
                                            clock_source=clock_tree.clock_source)

        # Verify routing_by_metal was loaded
        assert retrieved_clock_tree.routing_by_metal is not None
        assert isinstance(retrieved_clock_tree.routing_by_metal, dict)
        assert len(retrieved_clock_tree.routing_by_metal) == 2

        # Verify metal layers
        assert 'met1' in retrieved_clock_tree.routing_by_metal
        assert 'met2' in retrieved_clock_tree.routing_by_metal

        # Verify images match
        assert np.array_equal(routing_met1, retrieved_clock_tree.routing_by_metal['met1'])
        assert np.array_equal(routing_met2, retrieved_clock_tree.routing_by_metal['met2'])

    def test_routing_by_metal_empty_dict(self, temp_dir, sample_netlist_data):
        """Test that empty routing_by_metal dictionary is handled correctly."""
        db_path = Path(temp_dir) / "empty_routing_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        # Set routing_by_metal to empty dict
        netlist.routing_by_metal = {}

        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Add images (should handle empty dict gracefully)
        db.add_entity_images('netlists', netlist)
        db.close()

        # Retrieve entity
        retrieved = db.get_entity('netlists',
                                 flow_id=netlist.flow_id,
                                 stage=netlist.stage)

        # routing_by_metal should be an empty dict
        assert retrieved.routing_by_metal is not None
        assert isinstance(retrieved.routing_by_metal, dict)
        assert len(retrieved.routing_by_metal) == 0

    def test_filedb_routing_by_metal(self, temp_dir, sample_netlist_data):
        """Test routing_by_metal with FileDB backend."""
        from eda_schema.db import FileDB

        db_path = Path(temp_dir) / "filedb_routing"
        db = FileDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)

        # Create routing_by_metal dictionary
        routing_met1 = Image2D(np.random.rand(30, 30))
        routing_met2 = Image2D(np.random.rand(30, 30))

        netlist.routing_by_metal = {
            'met1': routing_met1,
            'met2': routing_met2,
        }

        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Add images
        db.add_entity_images('netlists', netlist)

        # Retrieve entity
        retrieved = db.get_entity('netlists',
                                 flow_id=netlist.flow_id,
                                 stage=netlist.stage)

        # Verify routing_by_metal was loaded
        assert retrieved.routing_by_metal is not None
        assert isinstance(retrieved.routing_by_metal, dict)
        assert len(retrieved.routing_by_metal) == 2
        assert 'met1' in retrieved.routing_by_metal
        assert 'met2' in retrieved.routing_by_metal
        assert np.array_equal(routing_met1, retrieved.routing_by_metal['met1'])
        assert np.array_equal(routing_met2, retrieved.routing_by_metal['met2'])


class TestErrorHandlingIntegration:
    """Test error handling in integrated workflows."""

    def test_missing_entity_graceful_handling(self, temp_dir, sample_netlist_data):
        """Test graceful handling of missing entities."""
        db_path = Path(temp_dir) / "error_handling_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        # Try to get non-existent entity
        with pytest.raises(DataNotFoundError):
            db.get_entity('netlists', flow_id='nonexistent', stage='floorplan')

        # Should still be able to add new entities after error
        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Close writers to ensure data is flushed to disk
        db.close()

        # Clear cache to ensure fresh read
        _load_arrow_table.cache_clear()

        # Create new DB instance to avoid cache issues
        db2 = ParquetDB(str(db_path))

        # Verify it was added
        retrieved = db2.get_entity('netlists',
                                  flow_id=netlist.flow_id,
                                  stage=netlist.stage)
        assert retrieved.flow_id == netlist.flow_id
        assert retrieved.stage == netlist.stage
