#!/usr/bin/env python3
"""
Example: Load and Inspect Dataset

Description: Demonstrates how to load an existing dataset and inspect
its structure, including available flows, stages, and entities.

Prerequisites:
- EDA-schema installed
- A dataset directory (or use ../data/minimal_dataset/)

Key Concepts:
- Dataset initialization
- Loading data
- Inspecting dataset structure
- Accessing entities

Usage:
    python examples/01_basics/03_load_dataset.py [dataset_path]

Output:
    Displays dataset structure and available data.

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


def load_dataset(dataset_path: str):
    """Load a dataset and return the Dataset object."""
    print("=" * 60)
    print("Loading Dataset")
    print("=" * 60)

    db_path = Path(dataset_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")

    print(f"Dataset path: {dataset_path}")

    # Initialize database
    db = ParquetDB(str(db_path))

    # Create dataset
    dataset = Dataset(db)

    # Load standard cells
    print("Loading standard cells...")
    try:
        dataset.load_standard_cells()
        print(f"  Loaded {len(dataset.standard_cells)} standard cells")
    except Exception as e:
        print(f"  Warning: Could not load standard cells: {e}")

    print()
    return dataset


def inspect_dataset_structure(dataset: Dataset):
    """Inspect the structure of a loaded dataset."""
    print("=" * 60)
    print("Dataset Structure")
    print("=" * 60)

    # Try to load all flows
    try:
        dataset.load()
        print(f"Loaded {len(dataset)} design flow(s)")
        print()

        # List all flows
        for flow_id, design_flow in dataset.items():
            print(f"Flow ID: {flow_id}")
            print(f"  Design: {design_flow.design}")
            print(f"  Run status: {design_flow.run_status}")
            print(f"  Stages: {list(design_flow.stages.keys())}")
            print()

            # Inspect first stage if available
            if design_flow.stages:
                first_stage_name = list(design_flow.stages.keys())[0]
                first_stage = design_flow.stages[first_stage_name]
                print(f"  Example stage ({first_stage_name}):")
                if first_stage.netlist:
                    netlist = first_stage.netlist
                    print(f"    Netlist: {netlist.no_of_cells} cells, {netlist.no_of_nets} nets")
                if first_stage.cell_metrics:
                    print(f"    Cell metrics: {first_stage.cell_metrics.no_of_total_cells} total cells")
                if first_stage.power_metrics:
                    print(f"    Power: {first_stage.power_metrics.total_power} W")
                print()

    except Exception as e:
        print(f"Could not load full dataset: {e}")
        print("This is normal if the dataset is empty or incomplete.")
        print()


def inspect_database_tables(dataset: Dataset):
    """Inspect what tables exist in the database."""
    print("=" * 60)
    print("Database Tables")
    print("=" * 60)

    # Try to get table data for common entities
    common_entities = [
        'design_flows',
        'design_stages',
        'netlists',
        'gates',
        'ports',
        'nets',
        'pins',
        'standard_cells'
    ]

    for entity_name in common_entities:
        try:
            df = dataset.db.get_table_data(entity_name)
            if not df.empty:
                print(f"{entity_name}: {len(df)} row(s)")
                # Show first few columns
                cols = list(df.columns)[:5]
                print(f"  Columns: {', '.join(cols)}")
                if len(df.columns) > 5:
                    print(f"  ... and {len(df.columns) - 5} more")
        except Exception as e:
            # Table might not exist or be empty
            pass

    print()


def load_specific_flow(dataset: Dataset, flow_id: str = None):
    """Load a specific design flow."""
    if flow_id is None:
        # Try to get first available flow
        try:
            flows_df = dataset.db.get_table_data('design_flows')
            if not flows_df.empty:
                flow_id = flows_df.iloc[0]['flow_id']
            else:
                print("No flows available in dataset")
                return
        except Exception as e:
            print(f"Could not determine available flows: {e}")
            return

    print("=" * 60)
    print(f"Loading Flow: {flow_id}")
    print("=" * 60)

    try:
        dataset.load(flow_id=flow_id)
        design_flow = dataset[flow_id]

        print(f"Design: {design_flow.design}")
        print(f"Stages: {list(design_flow.stages.keys())}")
        print()

        # Try to load a netlist from first stage
        if design_flow.stages:
            first_stage_name = list(design_flow.stages.keys())[0]
            try:
                netlist = dataset.load_netlist(flow_id, first_stage_name)
                print(f"Netlist from stage '{first_stage_name}':")
                print(f"  Cells: {netlist.no_of_cells}")
                print(f"  Nets: {netlist.no_of_nets}")
                print(f"  Pins: {netlist.no_of_pins}")
                print(f"  Utilization: {netlist.utilization:.2%}")
                if netlist.width and netlist.height:
                    print(f"  Size: {netlist.width} x {netlist.height}")
            except Exception as e:
                print(f"  Could not load netlist: {e}")

    except Exception as e:
        print(f"Error loading flow: {e}")

    print()


def main():
    """Main function."""
    # Determine dataset path
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        # Try to use minimal dataset or current directory
        minimal_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if minimal_path.exists():
            dataset_path = str(minimal_path)
            print(f"No dataset path provided, using: {dataset_path}\n")
        else:
            print("Usage: python 02_load_dataset.py <dataset_path>")
            print("\nOr create a minimal dataset first.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("EDA-Schema: Loading and Inspecting Dataset")
    print("=" * 60 + "\n")

    # Load dataset
    dataset = load_dataset(dataset_path)

    # Inspect structure
    inspect_dataset_structure(dataset)

    # Inspect database tables
    inspect_database_tables(dataset)

    # Try to load specific flow
    load_specific_flow(dataset)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try example 04_query_data.py to query specific entities")
    print("  - Explore the dataset structure further")
    print()


if __name__ == "__main__":
    main()
