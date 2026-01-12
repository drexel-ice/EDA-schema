#!/usr/bin/env python3
"""
Example: Filter and Query Dataset

Description: Demonstrates filtering and querying dataset data using various
techniques and patterns.

Prerequisites:
- EDA-schema installed
- A dataset directory

Key Concepts:
- Filtering by flow_id and stage
- Querying with pandas
- Advanced filtering
- Batch queries

Usage:
    python examples/03_datasets/02_filter_and_query.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def filter_by_flow_and_stage(dataset: Dataset):
    """Filter entities by flow_id and stage."""
    print("=" * 60)
    print("Filtering by Flow and Stage")
    print("=" * 60)

    # Get available flows
    try:
        flows_df = dataset.db.get_table_data('design_flows')
        if flows_df.empty:
            print("No flows available")
            return
 
        flow_id = flows_df.iloc[0]['flow_id']
        print(f"Using flow_id: {flow_id}")
 
        # Get stages for this flow
        stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
        if stages_df.empty:
            print("No stages available")
            return
 
        stage = stages_df.iloc[0]['stage']
        print(f"Using stage: {stage}\n")
 
        # Filter gates
        gates_df = dataset.db.get_table_data('gates', flow_id=flow_id, stage=stage)
        print(f"Gates for {flow_id}/{stage}: {len(gates_df)}")
        if not gates_df.empty:
            print("\nFirst 5 gates:")
            print(gates_df[['name', 'standard_cell', 'x_min', 'y_min']].head())
 
        # Filter ports
        ports_df = dataset.db.get_table_data('ports', flow_id=flow_id, stage=stage)
        print(f"\nPorts for {flow_id}/{stage}: {len(ports_df)}")
        if not ports_df.empty:
            print("\nPorts:")
            print(ports_df[['name', 'direction', 'x', 'y']].head())
 
        # Filter nets
        nets_df = dataset.db.get_table_data('nets', flow_id=flow_id, stage=stage)
        print(f"\nNets for {flow_id}/{stage}: {len(nets_df)}")
        if not nets_df.empty:
            print("\nFirst 5 nets:")
            print(nets_df[['name', 'is_special_net', 'no_of_fanouts']].head())
 
    except Exception as e:
        print(f"Error filtering: {e}")

    print()


def query_with_pandas(dataset: Dataset):
    """Use pandas operations for querying."""
    print("=" * 60)
    print("Querying with Pandas")
    print("=" * 60)

    try:
        # Get all gates
        gates_df = dataset.db.get_table_data('gates')

        if gates_df.empty:
            print("No gates available")
            return

        print(f"Total gates: {len(gates_df)}")

        # Filter by standard cell
        if 'standard_cell' in gates_df.columns:
            cell_counts = gates_df['standard_cell'].value_counts()
            print(f"\nStandard cell distribution:")
            print(cell_counts.head(10))

        # Filter by area
        if all(col in gates_df.columns for col in ['x_min', 'y_min', 'x_max', 'y_max']):
            gates_df['area'] = (gates_df['x_max'] - gates_df['x_min']) * \
                              (gates_df['y_max'] - gates_df['y_min'])

            large_gates = gates_df[gates_df['area'] > gates_df['area'].median()]
            print(f"\nGates larger than median area: {len(large_gates)}")

            avg_area = gates_df['area'].mean()
            print(f"Average gate area: {avg_area:.2f} um²")
 
        # Group by flow_id and stage
        if 'flow_id' in gates_df.columns and 'stage' in gates_df.columns:
            grouped = gates_df.groupby(['flow_id', 'stage']).size()
            print(f"\nGates per flow/stage:")
            print(grouped.head(10))

    except Exception as e:
        print(f"Error querying: {e}")

    print()


def advanced_filtering(dataset: Dataset):
    """Advanced filtering techniques."""
    print("=" * 60)
    print("Advanced Filtering")
    print("=" * 60)

    try:
        # Get gates
        gates_df = dataset.db.get_table_data('gates')
 
        if gates_df.empty:
            print("No gates available")
            return
 
        # Filter by multiple conditions
        if all(col in gates_df.columns for col in ['x_min', 'y_min', 'x_max', 'y_max']):
            gates_df['area'] = (gates_df['x_max'] - gates_df['x_min']) * \
                              (gates_df['y_max'] - gates_df['y_min'])
 
            # Large gates in specific region
            large_gates = gates_df[
                (gates_df['area'] > 10.0) &
                (gates_df['x_min'] > 0) &
                (gates_df['y_min'] > 0)
            ]
            print(f"Large gates in positive quadrant: {len(large_gates)}")
 
        # Filter by standard cell type
        if 'standard_cell' in gates_df.columns:
            nand_gates = gates_df[gates_df['standard_cell'].str.contains('NAND', na=False)]
            print(f"NAND gates: {len(nand_gates)}")
 
            inv_gates = gates_df[gates_df['standard_cell'].str.contains('INV', na=False)]
            print(f"INV gates: {len(inv_gates)}")
 
        # Get metrics for specific flow/stage
        try:
            flows_df = dataset.db.get_table_data('design_flows')
            if not flows_df.empty:
                flow_id = flows_df.iloc[0]['flow_id']
                stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
 
                if not stages_df.empty:
                    stage = stages_df.iloc[0]['stage']
 
                    # Get power metrics
                    try:
                        power = dataset.db.get_entity('power_metrics', 
                                                      flow_id=flow_id, 
                                                      stage=stage)
                        print(f"\nPower for {flow_id}/{stage}:")
                        print(f"  Total: {power.total_power:.4f} W")
                    except:
                        pass
 
                    # Get area metrics
                    try:
                        area = dataset.db.get_entity('area_metrics',
                                                     flow_id=flow_id,
                                                     stage=stage)
                        print(f"\nArea for {flow_id}/{stage}:")
                        print(f"  Total: {area.total_area:.2f} um²")
                    except:
                        pass
 
        except Exception as e:
            print(f"Error in advanced filtering: {e}")

    except Exception as e:
        print(f"Error: {e}")

    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 03_filter_and_query.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Filtering and Querying Dataset")
    print("=" * 60 + "\n")

    # Initialize dataset
    db = ParquetDB(str(dataset_path))
    dataset = Dataset(db)
    dataset.load_standard_cells()

    # Filter operations
    filter_by_flow_and_stage(dataset)
    query_with_pandas(dataset)
    advanced_filtering(dataset)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
