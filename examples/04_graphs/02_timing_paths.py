#!/usr/bin/env python3
"""
Example: Working with Timing Paths

Description: Demonstrates loading and analyzing timing path graphs.

Prerequisites:
- EDA-schema installed
- A dataset with timing path data

Key Concepts:
- Timing path entities
- Critical path analysis
- Path delay calculations
- Timing metrics

Usage:
    python examples/04_graphs/02_timing_paths.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def load_timing_paths(dataset: Dataset, flow_id: str, stage: str):
    """Load timing paths for a design stage."""
    print("=" * 60)
    print(f"Loading Timing Paths: {flow_id}/{stage}")
    print("=" * 60)

    try:
        netlist = dataset.load_netlist(flow_id, stage)
        timing_paths = dataset.load_timing_paths(flow_id, stage, netlist)

        print(f"Loaded {len(timing_paths)} timing path(s)")

        if not timing_paths:
            print("No timing paths available")
            return timing_paths

        # Show path types
        path_types = {}
        for path in timing_paths.values():
            path_type = path.path_type
            path_types[path_type] = path_types.get(path_type, 0) + 1

        print("\nPath types:")
        for path_type, count in path_types.items():
            print(f"  {path_type}: {count}")

        return timing_paths

    except Exception as e:
        print(f"Error loading timing paths: {e}")
        return {}


def analyze_critical_paths(timing_paths):
    """Analyze critical timing paths."""
    print("\n" + "=" * 60)
    print("Critical Path Analysis")
    print("=" * 60)

    critical_paths = [path for path in timing_paths.values() 
                     if path.is_critical_path]

    print(f"Critical paths: {len(critical_paths)}")

    if critical_paths:
        # Sort by arrival time (path delay)
        critical_paths.sort(key=lambda p: p.arrival_time, reverse=True)

        print("\nTop 5 critical paths:")
        for i, path in enumerate(critical_paths[:5], 1):
            print(f"\n  Path {i}:")
            print(f"    Arrival Time: {path.arrival_time:.4f} ns")
            print(f"    Required Time: {path.required_time:.4f} ns")
            print(f"    Slack: {path.slack:.4f} ns")
            print(f"    Startpoint: {path.startpoint}")
            print(f"    Endpoint: {path.endpoint}")
            print(f"    Type: {path.path_type}")
    else:
        print("No critical paths found")

    print()


def analyze_path_delays(timing_paths):
    """Analyze timing path delays."""
    print("=" * 60)
    print("Path Delay Analysis")
    print("=" * 60)

    if not timing_paths:
        print("No timing paths available")
        return

    delays = [path.arrival_time for path in timing_paths.values()]
    slacks = [path.slack for path in timing_paths.values()]

    print(f"Total paths: {len(delays)}")
    print(f"\nDelay statistics:")
    print(f"  Min: {min(delays):.4f} ns")
    print(f"  Max: {max(delays):.4f} ns")
    print(f"  Mean: {sum(delays)/len(delays):.4f} ns")

    print(f"\nSlack statistics:")
    print(f"  Min: {min(slacks):.4f} ns")
    print(f"  Max: {max(slacks):.4f} ns")
    print(f"  Mean: {sum(slacks)/len(slacks):.4f} ns")

    # Count violating paths
    violating = sum(1 for s in slacks if s < 0)
    print(f"\nViolating paths (slack < 0): {violating} ({100*violating/len(slacks):.1f}%)")

    print()


def analyze_path_structure(timing_paths):
    """Analyze timing path graph structure."""
    print("=" * 60)
    print("Path Structure Analysis")
    print("=" * 60)

    if not timing_paths:
        print("No timing paths available")
        return

    # Analyze startpoints and endpoints
    startpoints = set()
    endpoints = set()

    for path in timing_paths.values():
        startpoints.add(path.startpoint)
        endpoints.add(path.endpoint)

    print(f"Unique startpoints: {len(startpoints)}")
    print(f"Unique endpoints: {len(endpoints)}")

    # Find common endpoints
    endpoint_counts = {}
    for path in timing_paths.values():
        endpoint = path.endpoint
        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

    if endpoint_counts:
        most_common = sorted(endpoint_counts.items(), 
                           key=lambda x: x[1], 
                           reverse=True)[:5]
        print("\nMost common endpoints:")
        for endpoint, count in most_common:
            print(f"  {endpoint}: {count} paths")

    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 02_timing_paths.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Working with Timing Paths")
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

        # Try to find a stage with timing data
        stage = None
        for _, row in stages_df.iterrows():
            s = row['stage']
            try:
                timing = dataset.db.get_entity('timing_metrics', 
                                              flow_id=flow_id, 
                                              stage=s)
                if timing:
                    stage = s
                    break
            except:
                continue

        if not stage:
            stage = stages_df.iloc[0]['stage']

        # Load and analyze timing paths
        timing_paths = load_timing_paths(dataset, flow_id, stage)

        if timing_paths:
            analyze_critical_paths(timing_paths)
            analyze_path_delays(timing_paths)
            analyze_path_structure(timing_paths)

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
