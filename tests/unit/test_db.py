# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/unit/test_db.py
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
Tests for database backends.
"""
from pathlib import Path

import pytest

from eda_schema.db import ParquetDB, FileDB
from eda_schema import entity
from eda_schema.errors import DataNotFoundError


class TestParquetDB:
    """Test ParquetDB functionality."""

    def test_parquetdb_creation(self, temp_dir):
        """Test creating a ParquetDB."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        assert db is not None
        assert db.data_home == Path(db_path)

    def test_parquetdb_create_tables(self, temp_dir):
        """Test creating dataset tables."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()
        # Should not raise
        assert db is not None

    def test_parquetdb_add_table_row(self, temp_dir, sample_netlist_data):
        """Test adding a table row."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        db.close()

        # Should not raise
        assert db is not None

    def test_parquetdb_get_entity(self, temp_dir, sample_netlist_data):
        """Test getting an entity."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)
        db.close()

        retrieved = db.get_entity('netlists',
                                 flow_id=netlist.flow_id,
                                 stage=netlist.stage)
        assert retrieved is not None
        assert retrieved.flow_id == netlist.flow_id

    def test_parquetdb_get_entity_not_found(self, temp_dir):
        """Test getting a non-existent entity raises error."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        with pytest.raises(DataNotFoundError):
            db.get_entity('netlists', flow_id='nonexistent', stage='floorplan')

    def test_parquetdb_get_table_data(self, temp_dir, sample_netlist_data):
        """Test getting table data."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        db.close()

        df = db.get_table_data('netlists', flow_id=netlist.flow_id)
        assert df is not None
        assert len(df) == 1
        assert df.iloc[0]['flow_id'] == netlist.flow_id


class TestFileDB:
    """Test FileDB functionality."""

    def test_filedb_creation(self, temp_dir):
        """Test creating a FileDB."""
        db_path = Path(temp_dir) / "test_filedb"
        db = FileDB(str(db_path))
        assert db is not None
        assert db.data_home == Path(db_path)
        assert db.data_home.exists()

    def test_filedb_create_tables(self, temp_dir):
        """Test creating dataset tables."""
        db_path = Path(temp_dir) / "test_filedb"
        db = FileDB(str(db_path))
        db.create_dataset_tables()
        # Should not raise
        assert db is not None

    def test_filedb_add_table_row(self, temp_dir, sample_netlist_data):
        """Test adding a table row."""
        db_path = Path(temp_dir) / "test_filedb"
        db = FileDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())

        # Verify CSV file was created
        table_path = db._table_path('netlists')  # pylint: disable=protected-access
        assert table_path.exists()

    def test_filedb_get_entity(self, temp_dir, sample_netlist_data):
        """Test getting an entity."""
        db_path = Path(temp_dir) / "test_filedb"
        db = FileDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        retrieved = db.get_entity('netlists',
                                 flow_id=netlist.flow_id,
                                 stage=netlist.stage)
        assert retrieved is not None
        assert retrieved.flow_id == netlist.flow_id
        assert retrieved.stage == netlist.stage

    def test_filedb_get_entity_not_found(self, temp_dir):
        """Test getting a non-existent entity raises error."""
        db_path = Path(temp_dir) / "test_filedb"
        db = FileDB(str(db_path))
        db.create_dataset_tables()

        # FileDB raises ValueError when no rows match, not DataNotFoundError
        with pytest.raises(ValueError, match="No rows match filters"):
            db.get_entity('netlists', flow_id='nonexistent', stage='floorplan')

    def test_filedb_get_table_data(self, temp_dir, sample_netlist_data):
        """Test getting table data."""
        db_path = Path(temp_dir) / "test_filedb"
        db = FileDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())

        df = db.get_table_data('netlists', flow_id=netlist.flow_id)
        assert df is not None
        assert len(df) == 1
        assert df.iloc[0]['flow_id'] == netlist.flow_id

    def test_filedb_add_graph_data(self, temp_dir, sample_netlist_data):
        """Test adding graph data."""
        db_path = Path(temp_dir) / "test_filedb"
        db = FileDB(str(db_path))
        db.create_dataset_tables()

        netlist = entity.NetlistEntity(**sample_netlist_data)
        netlist.add_node('node1', type='GATE', entity=None)
        netlist.add_node('node2', type='GATE', entity=None)
        netlist.add_edge('node1', 'node2')

        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Verify graph JSON file was created
        graph_dir = db._graph_dir('netlists')  # pylint: disable=protected-access
        # FileDB uses resolved key format: flow_id=value__stage=value
        # (with / replaced by _)
        resolved_key = f"flow_id={netlist.flow_id}__stage={netlist.stage}".replace("/", "_")
        graph_file = graph_dir / f"{resolved_key}.json"
        assert graph_file.exists()

    def test_filedb_multiple_entities(self, temp_dir, sample_netlist_data,
                                     sample_power_metrics_data):
        """Test FileDB with multiple entity types."""
        db_path = Path(temp_dir) / "test_filedb"
        db = FileDB(str(db_path))
        db.create_dataset_tables()

        # Add netlist (with graph data)
        netlist = entity.NetlistEntity(**sample_netlist_data)
        db.add_table_row('netlists', netlist.get_tabular_data())
        graph_data = netlist.get_graph_data()
        db.add_graph_data('netlists', graph_data,
                         flow_id=netlist.flow_id, stage=netlist.stage)

        # Add power metrics (tabular only)
        power = entity.PowerMetricsEntity(**sample_power_metrics_data)
        db.add_table_row('power_metrics', power.get_tabular_data())

        # Retrieve both
        retrieved_netlist = db.get_entity('netlists',
                                         flow_id=netlist.flow_id,
                                         stage=netlist.stage)
        retrieved_power = db.get_entity('power_metrics',
                                       flow_id=power.flow_id,
                                       stage=power.stage)

        assert retrieved_netlist is not None
        assert retrieved_power is not None
        assert retrieved_netlist.flow_id == netlist.flow_id
        assert retrieved_power.flow_id == power.flow_id
