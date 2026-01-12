#!/usr/bin/env python3
"""
Example: Create a New Dataset

Description: Demonstrates how to create a new dataset from scratch,
including initializing the database, creating entities, and storing them.

Prerequisites:
- EDA-schema installed
- Understanding of entities and database backends

Key Concepts:
- Dataset initialization
- Database table creation
- Entity storage
- Graph data storage

Usage:
    python examples/01_basics/02_create_dataset.py [output_path]

Output:
    Creates a new dataset in the specified directory.

See Also:
    - Interactive Notebook: notebooks/tutorials/01_getting_started.ipynb
    - Tutorial: tutorials/01_getting_started/
    - User Guide: docs/guides/user_guide.md#working-with-datasets
    - How-To: docs/howto/load_data.md
"""

import sys
from pathlib import Path

from eda_schema import entity
from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def create_minimal_dataset(output_path: str):
    """Create a minimal dataset with sample data."""
    print("=" * 60)
    print("Creating Minimal Dataset")
    print("=" * 60)

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {output_dir}")

    # Initialize database
    db = ParquetDB(str(output_dir))
    db.create_dataset_tables()
    print("Created database tables")

    # Create dataset
    dataset = Dataset(db)

    # Create standard cells
    print("\nCreating standard cells...")
    nand_cell = entity.StandardCellEntity(
        name='NAND2_X1',
        width=0.5,
        height=2.0,
        no_of_input_pins=2,
        no_of_output_pins=1,
        is_sequential=False,
        is_inverter=False,
        is_buffer=False,
        is_filler=False,
        is_diode=False
    )
    dataset.standard_cells['NAND2_X1'] = nand_cell
    dataset.dump_standard_cells()
    print(f"  Added {len(dataset.standard_cells)} standard cell(s)")

    # Create design flow
    flow_id = 'test_flow_001'
    stage = 'floorplan'

    design_flow = entity.DesignFlowEntity(
        flow_id=flow_id,
        design='test_design',
        run_status='completed'
    )
    db.add_table_row('design_flows', design_flow.get_tabular_data())
    print(f"\nCreated design flow: {flow_id}")

    # Create netlist
    netlist = entity.NetlistEntity(
        flow_id=flow_id,
        stage=stage,
        no_of_inputs=2,
        no_of_outputs=1,
        no_of_cells=3,
        no_of_nets=4,
        no_of_pins=6,
        utilization=0.5,
        width=100.0,
        height=100.0
    )

    # Add nodes to netlist
    # Add ports
    clk_port = entity.PortEntity(
        flow_id=flow_id, stage=stage, name='clk',
        direction='INPUT', x=0.0, y=0.0
    )
    netlist.add_node('clk', type='PORT', entity=clk_port)

    out_port = entity.PortEntity(
        flow_id=flow_id, stage=stage, name='out',
        direction='OUTPUT', x=100.0, y=0.0
    )
    netlist.add_node('out', type='PORT', entity=out_port)

    # Add gates
    for i in range(3):
        gate = entity.GateEntity(
            flow_id=flow_id, stage=stage,
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
    netlist.add_edge('clk', 'U1')
    netlist.add_edge('U1', 'U2')
    netlist.add_edge('U2', 'U3')
    netlist.add_edge('U3', 'out')

    print(f"\nCreated netlist with {len(list(netlist.nodes))} nodes, {len(list(netlist.edges))} edges")

    # Store netlist
    db.add_table_row('netlists', netlist.get_tabular_data())
    graph_data = netlist.get_graph_data()
    db.add_graph_data('netlists', graph_data, flow_id=flow_id, stage=stage)

    # Store individual entities
    db.add_table_row('ports', clk_port.get_tabular_data())
    db.add_table_row('ports', out_port.get_tabular_data())

    for i in range(3):
        gate = entity.GateEntity(
            flow_id=flow_id, stage=stage,
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

    # Create metrics
    power_metrics = entity.PowerMetricsEntity(
        flow_id=flow_id, stage=stage,
        combinational_power=0.1,
        sequential_power=0.0,
        macro_power=0.0,
        internal_power=0.08,
        switching_power=0.02,
        leakage_power=0.01,
        total_power=0.21
    )
    db.add_table_row('power_metrics', power_metrics.get_tabular_data())

    area_metrics = entity.AreaMetricsEntity(
        flow_id=flow_id, stage=stage,
        combinational_cell_area=15.0,
        sequential_cell_area=0.0,
        buffer_area=0.0,
        inverter_area=0.0,
        filler_area=0.0,
        tap_cell_area=0.0,
        diode_area=0.0,
        macro_area=0.0,
        cell_area=15.0,
        total_area=10000.0
    )
    db.add_table_row('area_metrics', area_metrics.get_tabular_data())

    # Create design stage
    design_stage = entity.DesignStageEntity(
        flow_id=flow_id,
        stage=stage,
        run_status='completed'
    )
    db.add_table_row('design_stages', design_stage.get_tabular_data())

    # Close database
    db.close()

    print("\nDataset created successfully!")
    print(f"  Location: {output_dir}")
    print(f"  Flow ID: {flow_id}")
    print(f"  Stage: {stage}")
    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        # Default to examples data directory
        output_path = Path(__file__).parent.parent / "data" / "minimal_dataset"
        print(f"No output path provided, using: {output_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Creating New Dataset")
    print("=" * 60 + "\n")

    create_minimal_dataset(output_path)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try 03_load_dataset.py to load this dataset")
    print("  - Try 04_query_data.py to query the data")
    print()


if __name__ == "__main__":
    main()
