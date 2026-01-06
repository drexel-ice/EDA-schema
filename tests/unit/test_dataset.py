"""
Tests for Dataset class.
"""
from pathlib import Path

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
