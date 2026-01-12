#!/usr/bin/env python3
"""
Example: Using FileDB

Description: Demonstrates using FileDB backend for human-readable storage.

Prerequisites:
- EDA-schema installed

Key Concepts:
- FileDB initialization
- CSV table storage
- JSON graph storage
- Human-readable format

Usage:
    python examples/07_database_backends/02_filedb.py [output_path]
"""

import sys
from pathlib import Path

from eda_schema import entity
from eda_schema.dataset import Dataset
from eda_schema.db import FileDB


def demonstrate_filedb_basic(output_path: str):
    """Demonstrate basic FileDB usage."""
    print("=" * 60)
    print("FileDB: Basic Usage")
    print("=" * 60)

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize FileDB
    db = FileDB(str(output_dir))
    db.create_dataset_tables()
    print(f"Created FileDB at: {output_dir}")

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
    print(f"CSV file created at: {output_dir / 'gates' / 'table.csv'}")

    # Read data
    gates_df = db.get_table_data('gates')
    print(f"Retrieved {len(gates_df)} gates")
    print()


def demonstrate_graph_storage(output_path: str):
    """Demonstrate graph storage with FileDB."""
    print("=" * 60)
    print("FileDB: Graph Storage")
    print("=" * 60)

    output_dir = Path(output_path) / "graph_example"
    output_dir.mkdir(parents=True, exist_ok=True)

    db = FileDB(str(output_dir))
    db.create_dataset_tables()

    # Create netlist
    netlist = entity.NetlistEntity(
        flow_id='test',
        stage='test',
        no_of_inputs=2,
        no_of_outputs=1,
        no_of_cells=3,
        no_of_nets=2,
        no_of_pins=4,
        utilization=0.5,
        width=100.0,
        height=100.0
    )

    # Add nodes
    for i in range(3):
        gate = entity.GateEntity(
            flow_id='test',
            stage='test',
            name=f'U{i+1}',
            standard_cell='NAND2_X1',
            x_min=10.0 + i * 20.0,
            y_min=10.0,
            x_max=15.0 + i * 20.0,
            y_max=15.0,
            no_of_inputs=2,
            no_of_outputs=1
        )
        netlist.add_node(f'U{i+1}', type='GATE', entity=gate)

    # Add edges
    netlist.add_edge('U1', 'U2')
    netlist.add_edge('U2', 'U3')

    # Store
    db.add_table_row('netlists', netlist.get_tabular_data())
    graph_data = netlist.get_graph_data()
    db.add_graph_data('netlists', graph_data, flow_id='test', stage='test')

    print("Stored netlist with graph")
    print(f"Graph JSON at: {output_dir / 'netlists' / 'graphs'}")

    # Read back
    graph_data_read = db.get_graph_data('netlists', flow_id='test', stage='test')
    print(f"Retrieved graph with {len(graph_data_read['nodes'])} nodes")
    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = Path(__file__).parent.parent / "data" / "filedb_test"
        print(f"Using output path: {output_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: FileDB Backend")
    print("=" * 60 + "\n")

    demonstrate_filedb_basic(str(output_path))
    demonstrate_graph_storage(str(output_path))

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nKey Points:")
    print("  - Tables stored as CSV (human-readable)")
    print("  - Graphs stored as JSON")
    print("  - Good for debugging and small datasets")
    print()


if __name__ == "__main__":
    main()
