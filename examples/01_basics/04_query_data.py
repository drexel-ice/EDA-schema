#!/usr/bin/env python3
"""
Example: Query Data from Dataset

Description: Demonstrates how to query entities from a dataset using
various filters and access patterns.

Prerequisites:
- EDA-schema installed
- A dataset with data (or use ../data/minimal_dataset/)

Key Concepts:
- Querying table data
- Filtering by flow_id and stage
- Getting specific entities
- Working with pandas DataFrames

Usage:
    python examples/01_basics/04_query_data.py [dataset_path]

Output:
    Demonstrates various query operations and displays results.

See Also:
    - Interactive Notebook: notebooks/tutorials/03_loading_datasets.ipynb
    - Tutorial: tutorials/03_loading_datasets/
    - User Guide: docs/guides/user_guide.md#working-with-datasets
    - How-To: docs/howto/load_data.md
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def query_table_data(dataset: Dataset):
    """Query table data from the database."""
    print("=" * 60)
    print("Querying Table Data")
    print("=" * 60)

    # Get all gates
    try:
        gates_df = dataset.db.get_table_data('gates')
        if not gates_df.empty:
            print(f"Total gates in database: {len(gates_df)}")
            print(f"Columns: {list(gates_df.columns)}")
            print("\nFirst 5 gates:")
            print(gates_df.head())
            print()
        else:
            print("No gates found in database")
    except Exception as e:
        print(f"Could not query gates: {e}")

    print()


def query_with_filters(dataset: Dataset, flow_id: str = None, stage: str = None):
    """Query data with filters."""
    print("=" * 60)
    print("Querying with Filters")
    print("=" * 60)

    # Try to get a flow_id if not provided
    if flow_id is None:
        try:
            flows_df = dataset.db.get_table_data('design_flows')
            if not flows_df.empty:
                flow_id = flows_df.iloc[0]['flow_id']
                print(f"Using flow_id: {flow_id}")
            else:
                print("No flows available")
                return
        except Exception as e:
            print(f"Could not determine flow_id: {e}")
            return

    if stage is None:
        try:
            stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
            if not stages_df.empty:
                stage = stages_df.iloc[0]['stage']
                print(f"Using stage: {stage}")
        except Exception as e:
            print(f"Could not determine stage: {e}")
            return

    # Query gates for specific flow and stage
    try:
        gates_df = dataset.db.get_table_data('gates', flow_id=flow_id, stage=stage)
        if not gates_df.empty:
            print(f"\nGates for flow_id='{flow_id}', stage='{stage}': {len(gates_df)}")
            print("\nFirst 5 gates:")
            print(gates_df[['name', 'standard_cell', 'x_min', 'y_min']].head())
        else:
            print(f"No gates found for flow_id='{flow_id}', stage='{stage}'")
    except Exception as e:
        print(f"Error querying gates: {e}")

    # Query ports
    try:
        ports_df = dataset.db.get_table_data('ports', flow_id=flow_id, stage=stage)
        if not ports_df.empty:
            print(f"\nPorts for flow_id='{flow_id}', stage='{stage}': {len(ports_df)}")
            print("\nFirst 5 ports:")
            print(ports_df[['name', 'direction', 'x', 'y']].head())
        else:
            print(f"No ports found for flow_id='{flow_id}', stage='{stage}'")
    except Exception as e:
        print(f"Error querying ports: {e}")

    # Query nets
    try:
        nets_df = dataset.db.get_table_data('nets', flow_id=flow_id, stage=stage)
        if not nets_df.empty:
            print(f"\nNets for flow_id='{flow_id}', stage='{stage}': {len(nets_df)}")
            print("\nFirst 5 nets:")
            print(nets_df[['name', 'is_special_net', 'no_of_fanouts']].head())
        else:
            print(f"No nets found for flow_id='{flow_id}', stage='{stage}'")
    except Exception as e:
        print(f"Error querying nets: {e}")

    print()


def get_specific_entity(dataset: Dataset, flow_id: str = None, stage: str = None):
    """Get a specific entity by its primary key."""
    print("=" * 60)
    print("Getting Specific Entity")
    print("=" * 60)

    if flow_id is None or stage is None:
        try:
            flows_df = dataset.db.get_table_data('design_flows')
            if not flows_df.empty:
                flow_id = flows_df.iloc[0]['flow_id']
                stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
                if not stages_df.empty:
                    stage = stages_df.iloc[0]['stage']
        except Exception as e:
            print(f"Could not determine flow_id/stage: {e}")
            return

    # Try to get a specific gate
    try:
        gates_df = dataset.db.get_table_data('gates', flow_id=flow_id, stage=stage)
        if not gates_df.empty:
            gate_name = gates_df.iloc[0]['name']
            gate = dataset.db.get_entity('gates', flow_id=flow_id, stage=stage, name=gate_name)
 
            print(f"Retrieved gate: {gate.name}")
            print(f"  Standard cell: {gate.standard_cell}")
            print(f"  Position: ({gate.x_min}, {gate.y_min}) to ({gate.x_max}, {gate.y_max})")
            print(f"  Inputs: {gate.no_of_inputs}, Outputs: {gate.no_of_outputs}")
        else:
            print("No gates available to retrieve")
    except Exception as e:
        print(f"Error retrieving entity: {e}")

    print()


def query_metrics(dataset: Dataset, flow_id: str = None, stage: str = None):
    """Query metrics entities."""
    print("=" * 60)
    print("Querying Metrics")
    print("=" * 60)

    if flow_id is None or stage is None:
        try:
            flows_df = dataset.db.get_table_data('design_flows')
            if not flows_df.empty:
                flow_id = flows_df.iloc[0]['flow_id']
                stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
                if not stages_df.empty:
                    stage = stages_df.iloc[0]['stage']
        except Exception as e:
            print(f"Could not determine flow_id/stage: {e}")
            return

    # Power metrics
    try:
        power = dataset.db.get_entity('power_metrics', flow_id=flow_id, stage=stage)
        print("Power Metrics:")
        print(f"  Total power: {power.total_power} W")
        print(f"  Combinational: {power.combinational_power} W")
        print(f"  Sequential: {power.sequential_power} W")
        print(f"  Leakage: {power.leakage_power} W")
    except Exception as e:
        print(f"Could not retrieve power metrics: {e}")

    # Area metrics
    try:
        area = dataset.db.get_entity('area_metrics', flow_id=flow_id, stage=stage)
        print("\nArea Metrics:")
        print(f"  Total area: {area.total_area} um²")
        print(f"  Cell area: {area.cell_area} um²")
        print(f"  Combinational: {area.combinational_cell_area} um²")
        print(f"  Sequential: {area.sequential_cell_area} um²")
    except Exception as e:
        print(f"Could not retrieve area metrics: {e}")

    # Timing metrics
    try:
        timing = dataset.db.get_entity('timing_metrics', flow_id=flow_id, stage=stage)
        print("\nTiming Metrics:")
        print(f"  Worst slack: {timing.worst_slack} ns")
        print(f"  Total negative slack: {timing.total_negative_slack} ns")
        print(f"  Violating endpoints: {timing.no_of_violating_endpoints}")
    except Exception as e:
        print(f"Could not retrieve timing metrics: {e}")

    print()


def main():
    """Main function."""
    # Determine dataset path
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        minimal_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if minimal_path.exists():
            dataset_path = str(minimal_path)
            print(f"No dataset path provided, using: {dataset_path}\n")
        else:
            print("Usage: python 03_query_data.py <dataset_path>")
            print("\nOr create a minimal dataset first.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("EDA-Schema: Querying Data from Dataset")
    print("=" * 60 + "\n")

    # Load dataset
    db = ParquetDB(dataset_path)
    dataset = Dataset(db)
    dataset.load_standard_cells()

    # Query operations
    query_table_data(dataset)
    query_with_filters(dataset)
    get_specific_entity(dataset)
    query_metrics(dataset)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Explore examples/02_entities/ for entity-specific examples")
    print("  - Try examples/03_datasets/ for advanced dataset operations")
    print()


if __name__ == "__main__":
    main()
