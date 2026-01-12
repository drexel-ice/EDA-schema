#!/usr/bin/env python3
"""
Example: Using SQLitePickleDB

Description: Demonstrates using SQLitePickleDB backend.

Prerequisites:
- EDA-schema installed
- SQLite support

Key Concepts:
- SQLitePickleDB initialization
- SQL table storage
- Pickle graph storage
- SQL queries

Usage:
    python examples/07_database_backends/03_sqlitepkldb.py [output_path]
"""

import sys
from pathlib import Path

from eda_schema import entity
from eda_schema.dataset import Dataset
from eda_schema.db import SQLitePickleDB


def demonstrate_sqlitepkldb_basic(output_path: str):
    """Demonstrate basic SQLitePickleDB usage."""
    print("=" * 60)
    print("SQLitePickleDB: Basic Usage")
    print("=" * 60)

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize SQLitePickleDB
    db = SQLitePickleDB(str(output_dir))
    db.create_dataset_tables()
    print(f"Created SQLitePickleDB at: {output_dir}")
    print(f"SQLite DB: {output_dir / 'tabular.db'}")
    print(f"Graph directory: {output_dir / 'graph_dir'}")

    # Add data
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

    # Read data
    gates_df = db.get_table_data('gates')
    print(f"Retrieved {len(gates_df)} gates")
    print()


def demonstrate_sql_queries(output_path: str):
    """Demonstrate SQL queries."""
    print("=" * 60)
    print("SQLitePickleDB: SQL Queries")
    print("=" * 60)

    output_dir = Path(output_path) / "sql_example"
    output_dir.mkdir(parents=True, exist_ok=True)

    db = SQLitePickleDB(str(output_dir))
    db.create_dataset_tables()

    # Add gates
    for i in range(10):
        gate = entity.GateEntity(
            flow_id='test',
            stage='test',
            name=f'U{i}',
            standard_cell='NAND2_X1' if i % 2 == 0 else 'INV_X1',
            x_min=10.0 + i * 10.0,
            y_min=10.0,
            x_max=15.0 + i * 10.0,
            y_max=15.0,
            no_of_inputs=2,
            no_of_outputs=1
        )
        db.add_table_row('gates', gate.get_tabular_data())

    # Use SQL directly
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM gates")
    count = cursor.fetchone()[0]
    print(f"Total gates (SQL): {count}")

    cursor.execute("SELECT name, standard_cell FROM gates WHERE standard_cell = 'NAND2_X1'")
    nand_gates = cursor.fetchall()
    print(f"NAND gates (SQL): {len(nand_gates)}")

    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = Path(__file__).parent.parent / "data" / "sqlitepkldb_test"
        print(f"Using output path: {output_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: SQLitePickleDB Backend")
    print("=" * 60 + "\n")

    demonstrate_sqlitepkldb_basic(str(output_path))
    demonstrate_sql_queries(str(output_path))

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nKey Points:")
    print("  - Tables stored in SQLite (SQL queries possible)")
    print("  - Graphs stored as pickle files")
    print("  - Good for compatibility with SQL tools")
    print()


if __name__ == "__main__":
    main()
