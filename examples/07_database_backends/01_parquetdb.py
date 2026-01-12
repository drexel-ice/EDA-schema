#!/usr/bin/env python3
"""
Example: Using ParquetDB

Description: Demonstrates using ParquetDB backend for efficient columnar storage.

Prerequisites:
- EDA-schema installed
- PyArrow (for Parquet support)

Key Concepts:
- ParquetDB initialization
- Writer management
- Efficient storage
- Performance considerations

Usage:
    python examples/07_database_backends/01_parquetdb.py [output_path]

See Also:
    - Interactive Notebook: notebooks/tutorials/07_database_backends.ipynb
    - User Guide: docs/guides/user_guide.md#database-backends
"""

import sys
from pathlib import Path

from eda_schema import entity
from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def demonstrate_parquetdb_basic(output_path: str):
    """Demonstrate basic ParquetDB usage."""
    print("=" * 60)
    print("ParquetDB: Basic Usage")
    print("=" * 60)

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize ParquetDB
    db = ParquetDB(str(output_dir))
    db.create_dataset_tables()
    print(f"Created ParquetDB at: {output_dir}")

    # Add some data
    flow_id = 'test_flow'
    stage = 'floorplan'

    # Add gates
    for i in range(5):
        gate = entity.GateEntity(
            flow_id=flow_id,
            stage=stage,
            name=f'U{i+1}',
            standard_cell='NAND2_X1',
            x_min=10.0 + i * 20.0,
            y_min=10.0,
            x_max=15.0 + i * 20.0,
            y_max=15.0,
            no_of_inputs=2,
            no_of_outputs=1
        )
        db.add_table_row('gates', gate.get_tabular_data())

    print("Added 5 gates")

    # Close writers before reading
    db.close()
    print("Closed writers")

    # Read data
    gates_df = db.get_table_data('gates')
    print(f"Retrieved {len(gates_df)} gates")
    print()

    return db


def demonstrate_context_manager(output_path: str):
    """Demonstrate using ParquetDB with context manager."""
    print("=" * 60)
    print("ParquetDB: Context Manager")
    print("=" * 60)

    output_dir = Path(output_path) / "context_example"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use context manager for automatic cleanup
    with ParquetDB(str(output_dir)) as db:
        db.create_dataset_tables()
 
        # Add data
        gate = entity.GateEntity(
            flow_id='test',
            stage='test',
            name='U1',
            standard_cell='NAND2_X1',
            x_min=10.0,
            y_min=10.0,
            x_max=15.0,
            y_max=15.0,
            no_of_inputs=2,
            no_of_outputs=1
        )
        db.add_table_row('gates', gate.get_tabular_data())
 
        # Writers automatically closed on exit
        print("Data added, context manager will close writers")

    # Now we can read
    db2 = ParquetDB(str(output_dir))
    gates_df = db2.get_table_data('gates')
    print(f"Retrieved {len(gates_df)} gates after context exit")
    print()


def demonstrate_batch_operations(output_path: str):
    """Demonstrate batch operations with ParquetDB."""
    print("=" * 60)
    print("ParquetDB: Batch Operations")
    print("=" * 60)

    output_dir = Path(output_path) / "batch_example"
    output_dir.mkdir(parents=True, exist_ok=True)

    db = ParquetDB(str(output_dir))
    db.create_dataset_tables()

    # Batch insert gates
    gates_data = []
    for i in range(100):
        gate = entity.GateEntity(
            flow_id='batch_test',
            stage='test',
            name=f'U{i}',
            standard_cell='NAND2_X1',
            x_min=10.0 + i * 1.0,
            y_min=10.0,
            x_max=15.0 + i * 1.0,
            y_max=15.0,
            no_of_inputs=2,
            no_of_outputs=1
        )
        gates_data.append(gate.get_tabular_data())

    db.add_table_data('gates', gates_data)
    print(f"Batch inserted {len(gates_data)} gates")

    db.close()

    # Read back
    gates_df = db.get_table_data('gates')
    print(f"Retrieved {len(gates_df)} gates")
    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = Path(__file__).parent.parent / "data" / "parquetdb_test"
        print(f"Using output path: {output_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: ParquetDB Backend")
    print("=" * 60 + "\n")

    demonstrate_parquetdb_basic(str(output_path))
    demonstrate_context_manager(str(output_path))
    demonstrate_batch_operations(str(output_path))

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nKey Points:")
    print("  - Always close writers before reading")
    print("  - Use context manager for automatic cleanup")
    print("  - Batch operations are more efficient")
    print()


if __name__ == "__main__":
    main()
