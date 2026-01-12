"""
Tests for Dataset class.
"""
from pathlib import Path

import pytest

from eda_schema.dataset import Dataset, StandardCellData
from eda_schema.db import ParquetDB
from eda_schema import entity


class TestDataset:
    """Test Dataset functionality."""

    def test_dataset_creation(self, temp_dir):
        """Test creating a Dataset."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        dataset = Dataset(db)
        assert dataset is not None
        assert dataset.db == db

    def test_dataset_standard_cells(self, sample_dataset, sample_standard_cell_data):
        """Test Dataset standard cells management."""
        std_cell = entity.StandardCellEntity(**sample_standard_cell_data)
        sample_dataset.standard_cells.add_cell(std_cell)

        assert sample_standard_cell_data['name'] in sample_dataset.standard_cells
        retrieved = sample_dataset.standard_cells.get(sample_standard_cell_data['name'])
        assert retrieved is not None
        assert retrieved.name == std_cell.name

    def test_dataset_load_standard_cells(self, temp_dir, sample_standard_cell_data):
        """Test loading standard cells."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()
        dataset = Dataset(db)

        # Add standard cell to dataset
        std_cell = entity.StandardCellEntity(**sample_standard_cell_data)
        dataset.standard_cells.add_cell(std_cell)

        # Dump to database
        dataset.dump_standard_cells()
        db.close()

        # Create new dataset and load from database
        db2 = ParquetDB(str(db_path))
        dataset2 = Dataset(db2)
        dataset2.load_standard_cells()

        assert sample_standard_cell_data['name'] in dataset2.standard_cells

    def test_dataset_save_load_pickle(self, temp_dir, sample_dataset, sample_netlist_data):
        """Test saving and loading dataset from pickle."""
        pickle_path = Path(temp_dir) / "dataset.pkl"

        # Add some data
        netlist = entity.NetlistEntity(**sample_netlist_data)
        design_flow = entity.DesignFlowEntity(
            flow_id='test_flow',
            design='test_design',
            stages={}
        )
        sample_dataset['test_flow'] = design_flow

        sample_dataset.save_to_pickle(str(pickle_path))
        assert pickle_path.exists()

        # Load it back
        db2 = ParquetDB(str(Path(temp_dir) / "test_db2"))
        loaded = Dataset.load_from_pickle(str(pickle_path), db2)
        assert loaded is not None
        assert loaded.db == db2
        assert 'test_flow' in loaded

    def test_dataset_dump_standard_cells_empty(self, sample_dataset):
        """Test dumping empty standard cells."""
        # Should not raise
        sample_dataset.dump_standard_cells()

    def test_dataset_load_standard_cells_empty(self, temp_dir):
        """Test loading standard cells from empty database."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()
        dataset = Dataset(db)

        # Should not raise
        dataset.load_standard_cells()
        assert len(dataset.standard_cells) == 0


class TestStandardCellData:
    """Test StandardCellData functionality."""

    def test_standard_cell_data_creation(self):
        """Test creating StandardCellData."""
        std_cell_data = StandardCellData()
        assert std_cell_data is not None
        assert isinstance(std_cell_data, dict)
        assert isinstance(std_cell_data.seq_cells, list)

    def test_standard_cell_data_add_cell(self, sample_standard_cell_data):
        """Test adding a standard cell."""
        std_cell_data = StandardCellData()
        std_cell = entity.StandardCellEntity(**sample_standard_cell_data)
        std_cell_data.add_cell(std_cell)

        assert sample_standard_cell_data['name'] in std_cell_data
        assert isinstance(std_cell_data.seq_cells, list)

    def test_standard_cell_data_add_sequential_cell(self, sample_standard_cell_data):
        """Test adding a sequential cell updates seq_cells list."""
        std_cell_data = StandardCellData()
        std_cell = entity.StandardCellEntity(**sample_standard_cell_data)
        std_cell.is_sequential = True
        std_cell_data.add_cell(std_cell)

        assert std_cell.name in std_cell_data.seq_cells

    def test_standard_cell_data_add_non_sequential_cell(self, sample_standard_cell_data):
        """Test adding a non-sequential cell doesn't update seq_cells."""
        std_cell_data = StandardCellData()
        std_cell = entity.StandardCellEntity(**sample_standard_cell_data)
        std_cell.is_sequential = False
        initial_len = len(std_cell_data.seq_cells)
        std_cell_data.add_cell(std_cell)

        # seq_cells should not change for non-sequential cells
        assert len(std_cell_data.seq_cells) == initial_len

    def test_standard_cell_data_add_cell_updates_dict(self, sample_standard_cell_data):
        """Test that add_cell updates the dictionary."""
        std_cell_data = StandardCellData()
        std_cell = entity.StandardCellEntity(**sample_standard_cell_data)
        std_cell_data.add_cell(std_cell)

        # Check it's in the dict
        assert std_cell.name in std_cell_data
        assert std_cell_data[std_cell.name] == std_cell

    def test_dataset_dump_empty_flows(self, temp_dir):
        """Test dump raises error when dataset has no flows."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        dataset = Dataset(db)

        with pytest.raises(ValueError, match="no flows"):
            dataset.dump()

    def test_dataset_dump_none_flow(self, temp_dir):
        """Test dump raises error when flow entry is None."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        dataset = Dataset(db)
        dataset['test_flow'] = None

        with pytest.raises(ValueError, match="empty design flow entry"):
            dataset.dump()

    def test_dataset_dump_design_stage_none_netlist(self, temp_dir):
        """Test dump_design_stage handles None netlist."""
        db_path = Path(temp_dir) / "test_db"
        db = ParquetDB(str(db_path))
        db.create_dataset_tables()
        dataset = Dataset(db)

        # Create design stage with None netlist
        design_stage = entity.DesignStageEntity(
            flow_id='test_flow',
            stage='floorplan',
            netlist=None
        )
        design_flow = entity.DesignFlowEntity(
            flow_id='test_flow',
            design='test_design',
            stages={'floorplan': design_stage}
        )
        dataset['test_flow'] = design_flow

        # Should not raise
        dataset.dump_design_stage(design_stage, 'test_flow', 'floorplan')
