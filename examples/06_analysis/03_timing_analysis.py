#!/usr/bin/env python3
"""
Example: Timing Analysis

Description: Demonstrates analyzing timing metrics and critical paths.

Prerequisites:
- EDA-schema installed
- A dataset with timing data

Key Concepts:
- Timing metrics analysis
- Critical path identification
- Slack analysis
- Timing violations

Usage:
    python examples/06_analysis/03_timing_analysis.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def analyze_timing_metrics(dataset: Dataset, flow_id: str, stage: str):
    """Analyze timing metrics."""
    print("=" * 60)
    print(f"Timing Metrics: {flow_id}/{stage}")
    print("=" * 60)

    try:
        timing = dataset.db.get_entity('timing_metrics', flow_id=flow_id, stage=stage)
 
        print("Timing Summary:")
        print(f"  Worst Slack: {timing.worst_slack:.4f} ns")
        print(f"  Total Negative Slack: {timing.total_negative_slack:.4f} ns")
        print(f"  Worst Arrival Time: {timing.worst_arrival_time:.4f} ns")
        print(f"  Worst Required Time: {timing.worst_required_time:.4f} ns")
        print(f"  Total Endpoints: {timing.no_of_endpoints}")
        print(f"  Violating Endpoints: {timing.no_of_violating_endpoints}")
 
        if timing.no_of_endpoints > 0:
            violation_rate = (timing.no_of_violating_endpoints / 
                            timing.no_of_endpoints) * 100
            print(f"  Violation Rate: {violation_rate:.2f}%")
 
        if timing.critical_path_startpoint and timing.critical_path_endpoint:
            print(f"\nCritical Path:")
            print(f"  Startpoint: {timing.critical_path_startpoint}")
            print(f"  Endpoint: {timing.critical_path_endpoint}")
 
        # Timing status
        if timing.worst_slack >= 0:
            print("\n✓ Timing: MET")
        else:
            print(f"\n✗ Timing: VIOLATED (by {abs(timing.worst_slack):.4f} ns)")
 
        print()

    except Exception as e:
        print(f"Error analyzing timing: {e}")


def analyze_critical_paths(dataset: Dataset, flow_id: str, stage: str):
    """Analyze critical timing paths."""
    print("=" * 60)
    print("Critical Path Analysis")
    print("=" * 60)

    try:
        netlist = dataset.load_netlist(flow_id, stage)
        timing_paths = dataset.load_timing_paths(flow_id, stage, netlist)
 
        if not timing_paths:
            print("No timing paths available")
            return
 
        critical_paths = [p for p in timing_paths.values() if p.is_critical_path]
 
        print(f"Total paths: {len(timing_paths)}")
        print(f"Critical paths: {len(critical_paths)}")
 
        if critical_paths:
            # Sort by delay
            critical_paths.sort(key=lambda p: p.path_delay, reverse=True)
 
            print("\nTop 5 Critical Paths:")
            for i, path in enumerate(critical_paths[:5], 1):
                print(f"\n  Path {i}:")
                print(f"    Delay: {path.path_delay:.4f} ns")
                print(f"    Slack: {path.path_slack:.4f} ns")
                print(f"    Type: {path.path_type}")
                print(f"    Startpoint: {path.startpoint}")
                print(f"    Endpoint: {path.endpoint}")
 
        # Analyze path delays
        all_delays = [p.path_delay for p in timing_paths.values()]
        all_slacks = [p.path_slack for p in timing_paths.values()]
 
        print(f"\nPath Delay Statistics:")
        print(f"  Min: {min(all_delays):.4f} ns")
        print(f"  Max: {max(all_delays):.4f} ns")
        print(f"  Mean: {sum(all_delays)/len(all_delays):.4f} ns")
 
        print(f"\nSlack Statistics:")
        print(f"  Min: {min(all_slacks):.4f} ns")
        print(f"  Max: {max(all_slacks):.4f} ns")
        print(f"  Mean: {sum(all_slacks)/len(all_slacks):.4f} ns")
 
        violating = sum(1 for s in all_slacks if s < 0)
        print(f"  Violating paths: {violating} ({100*violating/len(all_slacks):.1f}%)")
 
        print()

    except Exception as e:
        print(f"Error analyzing critical paths: {e}")


def compare_timing_across_stages(dataset: Dataset, flow_id: str):
    """Compare timing across design stages."""
    print("=" * 60)
    print("Timing Comparison Across Stages")
    print("=" * 60)

    try:
        stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
 
        if stages_df.empty:
            print("No stages available")
            return
 
        stages = stages_df['stage'].tolist()
 
        print(f"{'Stage':<20} {'Worst Slack (ns)':<20} {'Violations':<15} {'Endpoints':<15}")
        print("-" * 70)
 
        for stage in stages:
            try:
                timing = dataset.db.get_entity('timing_metrics',
                                              flow_id=flow_id,
                                              stage=stage)
                print(f"{stage:<20} {timing.worst_slack:<20.4f} "
                      f"{timing.no_of_violating_endpoints:<15} "
                      f"{timing.no_of_endpoints:<15}")
            except:
                print(f"{stage:<20} {'N/A':<20} {'N/A':<15} {'N/A':<15}")
 
        print()

    except Exception as e:
        print(f"Error comparing timing: {e}")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 03_timing_analysis.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Timing Analysis")
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
 
        stage = stages_df.iloc[0]['stage']
 
        analyze_timing_metrics(dataset, flow_id, stage)
        analyze_critical_paths(dataset, flow_id, stage)
        compare_timing_across_stages(dataset, flow_id)

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
