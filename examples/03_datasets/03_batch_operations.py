#!/usr/bin/env python3
"""
Example: Batch Operations

Description: Demonstrates performing batch operations on datasets,
including batch insertion, updates, and bulk queries.

Prerequisites:
- EDA-schema installed
- Understanding of dataset operations

Key Concepts:
- Batch data insertion
- Bulk queries
- Efficient data processing
- Performance optimization

Usage:
    python examples/03_datasets/03_batch_operations.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema import entity
from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def batch_insert_entities(output_path: str):
    """Demonstrate batch insertion of entities."""
    print("=" * 60)
    print("Batch Insertion")
    print("=" * 60)

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    db = ParquetDB(str(output_dir))
    db.create_dataset_tables()

    flow_id = 'batch_test'
    stage = 'floorplan'

    # Create multiple gates
    gates_data = []
    for i in range(10):
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
        gates_data.append(gate.get_tabular_data())

    # Batch insert
    db.add_table_data('gates', gates_data)
    print(f"Batch inserted {len(gates_data)} gates")

    # Create multiple ports
    ports_data = []
    port_names = ['clk', 'reset', 'data_in', 'data_out', 'valid']
    for i, name in enumerate(port_names):
        port = entity.PortEntity(
            flow_id=flow_id,
            stage=stage,
            name=name,
            direction='INPUT' if i < 3 else 'OUTPUT',
            x=0.0 if i < 3 else 100.0,
            y=i * 10.0
        )
        ports_data.append(port.get_tabular_data())

    db.add_table_data('ports', ports_data)
    print(f"Batch inserted {len(ports_data)} ports")

    db.close()
    print(f"\nBatch operations completed. Dataset saved to: {output_dir}")
    print()


def batch_query_entities(dataset: Dataset):
    """Demonstrate batch querying."""
    print("=" * 60)
    print("Batch Querying")
    print("=" * 60)

    try:
        # Get all entities of a type
        gates_df = dataset.db.get_table_data('gates')
        print(f"Total gates: {len(gates_df)}")

        if not gates_df.empty:
            # Process in batches
            batch_size = 100
            total_batches = (len(gates_df) + batch_size - 1) // batch_size

            print(f"Processing {len(gates_df)} gates in {total_batches} batch(es)")

            for i in range(0, len(gates_df), batch_size):
                batch = gates_df.iloc[i:i+batch_size]
                print(f"  Batch {i//batch_size + 1}: {len(batch)} gates")

        # Get multiple entity types
        entity_types = ['gates', 'ports', 'nets', 'pins']
        for entity_type in entity_types:
            try:
                df = dataset.db.get_table_data(entity_type)
                print(f"{entity_type}: {len(df)} entities")
            except:
                print(f"{entity_type}: not available")

    except Exception as e:
        print(f"Error in batch querying: {e}")

    print()


def process_multiple_stages(dataset: Dataset):
    """Process data across multiple stages."""
    print("=" * 60)
    print("Processing Multiple Stages")
    print("=" * 60)

    try:
        # Get all flows
        flows_df = dataset.db.get_table_data('design_flows')

        if flows_df.empty:
            print("No flows available")
            return

        # Process each flow
        for _, flow_row in flows_df.iterrows():
            flow_id = flow_row['flow_id']
            print(f"\nProcessing flow: {flow_id}")

            # Get stages for this flow
            stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)

            if stages_df.empty:
                print("  No stages available")
                continue

            # Process each stage
            for _, stage_row in stages_df.iterrows():
                stage = stage_row['stage']

                # Get gates for this stage
                try:
                    gates_df = dataset.db.get_table_data('gates',
                                                        flow_id=flow_id,
                                                        stage=stage)
                    print(f"  {stage}: {len(gates_df)} gates")
                except:
                    print(f"  {stage}: no gates")

    except Exception as e:
        print(f"Error processing stages: {e}")

    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        # Create a test dataset for batch operations
        dataset_path = Path(__file__).parent.parent / "data" / "batch_test"
        print(f"Creating test dataset at: {dataset_path}\n")
        batch_insert_entities(str(dataset_path))

    print("\n" + "=" * 60)
    print("EDA-Schema: Batch Operations")
    print("=" * 60 + "\n")

    # Load dataset for querying
    if Path(dataset_path).exists():
        db = ParquetDB(str(dataset_path))
        dataset = Dataset(db)
        dataset.load_standard_cells()

        batch_query_entities(dataset)
        process_multiple_stages(dataset)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
