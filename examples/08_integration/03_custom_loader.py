#!/usr/bin/env python3
"""
Example: Custom Data Loader

Description: Demonstrates creating a custom data loader for importing
data from external sources.

Prerequisites:
- EDA-schema installed
- Understanding of entity structure

Key Concepts:
- Custom loader design
- Data transformation
- Entity creation patterns
- Integration architecture

Usage:
    python examples/08_integration/03_custom_loader.py [output_path]
"""

import sys
from pathlib import Path

from eda_schema import entity
from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def custom_data_loader_example(output_path: str):
    """Example of a custom data loader."""
    print("=" * 60)
    print("Custom Data Loader Example")
    print("=" * 60)

    print("""
Custom Loader Pattern:

1. Parse your data format
2. Transform to EDA-schema entities
3. Store in database

Example structure:
""")

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database
    db = ParquetDB(str(output_dir))
    db.create_dataset_tables()
    dataset = Dataset(db)

    # Simulate parsing external data
    print("Step 1: Parse external data format")
    external_data = {
        'cells': [
            {'name': 'cell1', 'type': 'NAND2', 'x': 10, 'y': 20, 'w': 5, 'h': 5},
            {'name': 'cell2', 'type': 'INV', 'x': 30, 'y': 20, 'w': 3, 'h': 5},
        ],
        'nets': [
            {'name': 'net1', 'source': 'cell1', 'sinks': ['cell2']},
        ],
        'ports': [
            {'name': 'clk', 'direction': 'INPUT', 'x': 0, 'y': 0},
        ]
    }
    print(f"  Parsed {len(external_data['cells'])} cells")
    print(f"  Parsed {len(external_data['nets'])} nets")
    print(f"  Parsed {len(external_data['ports'])} ports")

    # Transform to entities
    print("\nStep 2: Transform to EDA-schema entities")
    flow_id = 'custom_import'
    stage = 'floorplan'

    # Create gates
    for cell_data in external_data['cells']:
        gate = entity.GateEntity(
            flow_id=flow_id,
            stage=stage,
            name=cell_data['name'],
            standard_cell=cell_data['type'] + '_X1',
            x_min=float(cell_data['x']),
            y_min=float(cell_data['y']),
            x_max=float(cell_data['x'] + cell_data['w']),
            y_max=float(cell_data['y'] + cell_data['h']),
            no_of_inputs=2 if 'NAND' in cell_data['type'] else 1,
            no_of_outputs=1
        )
        db.add_table_row('gates', gate.get_tabular_data())
        print(f"  Created gate: {gate.name}")

    # Create ports
    for port_data in external_data['ports']:
        port = entity.PortEntity(
            flow_id=flow_id,
            stage=stage,
            name=port_data['name'],
            direction=port_data['direction'],
            x=float(port_data['x']),
            y=float(port_data['y'])
        )
        db.add_table_row('ports', port.get_tabular_data())
        print(f"  Created port: {port.name}")

    # Create nets
    for net_data in external_data['nets']:
        net = entity.NetEntity(
            flow_id=flow_id,
            stage=stage,
            name=net_data['name'],
            is_special_net=False,
            no_of_fanouts=len(net_data['sinks']),
            x_min=0.0,
            y_min=0.0,
            x_max=100.0,
            y_max=100.0,
            length=50.0
        )
        db.add_table_row('nets', net.get_tabular_data())
        print(f"  Created net: {net.name}")

    # Store
    print("\nStep 3: Store in database")
    db.close()
    print(f"  Saved to: {output_dir}")

    # Verify
    print("\nStep 4: Verify import")
    db2 = ParquetDB(str(output_dir))
    gates_df = db2.get_table_data('gates')
    print(f"  Retrieved {len(gates_df)} gates")
    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = Path(__file__).parent.parent / "data" / "custom_loader_test"
        print(f"Using output path: {output_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Custom Data Loader")
    print("=" * 60 + "\n")

    custom_data_loader_example(str(output_path))

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nKey Points:")
    print("  - Parse your data format")
    print("  - Transform to EDA-schema entities")
    print("  - Store using database backend")
    print("  - Verify import")
    print()


if __name__ == "__main__":
    main()

