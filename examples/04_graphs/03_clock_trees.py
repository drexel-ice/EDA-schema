#!/usr/bin/env python3
"""
Example: Working with Clock Trees

Description: Demonstrates loading and analyzing clock tree structures.

Prerequisites:
- EDA-schema installed
- A dataset with clock tree data

Key Concepts:
- Clock tree entities
- Clock network analysis
- Clock tree structure
- Clock distribution

Usage:
    python examples/04_graphs/03_clock_trees.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def load_clock_trees(dataset: Dataset, flow_id: str, stage: str):
    """Load clock trees for a design stage."""
    print("=" * 60)
    print(f"Loading Clock Trees: {flow_id}/{stage}")
    print("=" * 60)

    try:
        netlist = dataset.load_netlist(flow_id, stage)
        clock_trees = dataset.load_clock_trees(flow_id, stage, netlist)
 
        print(f"Loaded {len(clock_trees)} clock tree(s)")
 
        if not clock_trees:
            print("No clock trees available")
            return clock_trees
 
        for clock_name, clock_tree in clock_trees.items():
            print(f"\nClock: {clock_name}")
            print(f"  Source: {clock_tree.clock_source}")
            print(f"  Buffers: {clock_tree.no_of_buffers}")
            print(f"  Sinks: {clock_tree.no_of_clock_sinks}")
 
        return clock_trees

    except Exception as e:
        print(f"Error loading clock trees: {e}")
        return {}


def analyze_clock_tree_structure(clock_trees):
    """Analyze clock tree structure."""
    print("\n" + "=" * 60)
    print("Clock Tree Structure Analysis")
    print("=" * 60)

    if not clock_trees:
        print("No clock trees available")
        return

    total_buffers = 0
    total_sinks = 0

    for clock_name, clock_tree in clock_trees.items():
        total_buffers += clock_tree.no_of_buffers
        total_sinks += clock_tree.no_of_clock_sinks
 
        print(f"\n{clock_name}:")
        print(f"  Buffers: {clock_tree.no_of_buffers}")
        print(f"  Sinks: {clock_tree.no_of_clock_sinks}")
 
        if clock_tree.no_of_buffers > 0:
            avg_sinks_per_buffer = clock_tree.no_of_clock_sinks / clock_tree.no_of_buffers
            print(f"  Avg sinks per buffer: {avg_sinks_per_buffer:.1f}")

    print(f"\nTotal across all clocks:")
    print(f"  Buffers: {total_buffers}")
    print(f"  Sinks: {total_sinks}")
    print()


def query_clock_tree_entities(dataset: Dataset, flow_id: str, stage: str):
    """Query clock tree entities from database."""
    print("=" * 60)
    print("Querying Clock Tree Entities")
    print("=" * 60)

    try:
        clock_trees_df = dataset.db.get_table_data('clock_trees', 
                                                   flow_id=flow_id, 
                                                   stage=stage)
 
        if clock_trees_df.empty:
            print("No clock tree entities in database")
            return
 
        print(f"Clock tree entities: {len(clock_trees_df)}")
        print("\nClock trees:")
        for _, row in clock_trees_df.iterrows():
            print(f"  {row.get('clock_source', 'unknown')}: "
                  f"{row.get('no_of_buffers', 0)} buffers, "
                  f"{row.get('no_of_clock_sinks', 0)} sinks")

    except Exception as e:
        print(f"Error querying clock trees: {e}")

    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 03_clock_trees.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Working with Clock Trees")
    print("=" * 60 + "\n")

    # Load dataset
    db = ParquetDB(str(dataset_path))
    dataset = Dataset(db)
    dataset.load_standard_cells()

    try:
        flows_df = dataset.db.get_table_data('design_flows')
        if flows_df.empty:
            print("No flows available")
            return
 
        flow_id = flows_df.iloc[0]['flow_id']
        stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
 
        if stages_df.empty:
            print("No stages available")
            return
 
        # Try to find a stage with clock tree data (usually cts or later)
        stage = None
        for _, row in stages_df.iterrows():
            s = row['stage']
            if s in ['cts', 'global_route', 'detailed_route', 'final']:
                try:
                    clock_df = dataset.db.get_table_data('clock_trees',
                                                        flow_id=flow_id,
                                                        stage=s)
                    if not clock_df.empty:
                        stage = s
                        break
                except:
                    continue
 
        if not stage:
            stage = stages_df.iloc[0]['stage']
 
        # Load and analyze clock trees
        clock_trees = load_clock_trees(dataset, flow_id, stage)
 
        if clock_trees:
            analyze_clock_tree_structure(clock_trees)
 
        query_clock_tree_entities(dataset, flow_id, stage)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
