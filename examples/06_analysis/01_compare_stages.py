#!/usr/bin/env python3
"""
Example: Compare Design Stages

Description: Demonstrates comparing metrics across different design stages
to track design evolution.

Prerequisites:
- EDA-schema installed
- A dataset with multiple design stages

Key Concepts:
- Stage comparison
- Metrics tracking
- Design evolution analysis
- Trend identification

Usage:
    python examples/06_analysis/01_compare_stages.py [dataset_path]

See Also:
    - Interactive Notebook: notebooks/tutorials/06_analysis_workflows.ipynb
    - User Guide: docs/guides/user_guide.md#common-use-cases
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def compare_stages_for_flow(dataset: Dataset, flow_id: str):
    """Compare metrics across stages for a design flow."""
    print("=" * 60)
    print(f"Comparing Stages for Flow: {flow_id}")
    print("=" * 60)

    try:
        stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
 
        if stages_df.empty:
            print("No stages available")
            return
 
        stages = stages_df['stage'].tolist()
        print(f"Stages: {stages}\n")
 
        # Compare metrics
        print("Stage Comparison:")
        print(f"{'Stage':<20} {'Cells':<10} {'Area (um²)':<15} {'Power (W)':<15} {'Worst Slack (ns)':<20}")
        print("-" * 80)
 
        for stage in stages:
            try:
                # Get metrics
                cell_metrics = dataset.db.get_entity('cell_metrics', 
                                                     flow_id=flow_id, 
                                                     stage=stage)
                area_metrics = dataset.db.get_entity('area_metrics',
                                                    flow_id=flow_id,
                                                    stage=stage)
                power_metrics = dataset.db.get_entity('power_metrics',
                                                     flow_id=flow_id,
                                                     stage=stage)
                timing_metrics = dataset.db.get_entity('timing_metrics',
                                                      flow_id=flow_id,
                                                      stage=stage)
 
                cells = cell_metrics.no_of_total_cells
                area = area_metrics.total_area
                power = power_metrics.total_power
                slack = timing_metrics.worst_slack
 
                print(f"{stage:<20} {cells:<10} {area:<15.2f} {power:<15.4f} {slack:<20.4f}")
 
            except Exception as e:
                print(f"{stage:<20} {'N/A':<10} {'N/A':<15} {'N/A':<15} {'N/A':<20}")
 
        print()

    except Exception as e:
        print(f"Error comparing stages: {e}")


def analyze_trends(dataset: Dataset, flow_id: str):
    """Analyze trends across stages."""
    print("=" * 60)
    print("Trend Analysis")
    print("=" * 60)

    try:
        stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
 
        if stages_df.empty:
            return
 
        # Define stage order
        stage_order = ['floorplan', 'global_place', 'detailed_place', 
                      'cts', 'global_route', 'detailed_route', 'final']
 
        stages = [s for s in stage_order if s in stages_df['stage'].values]
 
        if len(stages) < 2:
            print("Need at least 2 stages for trend analysis")
            return
 
        # Track metrics
        areas = []
        powers = []
        slacks = []
 
        for stage in stages:
            try:
                area = dataset.db.get_entity('area_metrics',
                                            flow_id=flow_id,
                                            stage=stage).total_area
                power = dataset.db.get_entity('power_metrics',
                                             flow_id=flow_id,
                                             stage=stage).total_power
                slack = dataset.db.get_entity('timing_metrics',
                                             flow_id=flow_id,
                                             stage=stage).worst_slack
 
                areas.append(area)
                powers.append(power)
                slacks.append(slack)
            except:
                continue
 
        if len(areas) >= 2:
            print("\nArea Trend:")
            area_change = ((areas[-1] - areas[0]) / areas[0]) * 100
            print(f"  Initial: {areas[0]:.2f} um²")
            print(f"  Final: {areas[-1]:.2f} um²")
            print(f"  Change: {area_change:+.2f}%")
 
            print("\nPower Trend:")
            power_change = ((powers[-1] - powers[0]) / powers[0]) * 100
            print(f"  Initial: {powers[0]:.4f} W")
            print(f"  Final: {powers[-1]:.4f} W")
            print(f"  Change: {power_change:+.2f}%")
 
            print("\nTiming Trend:")
            slack_change = slacks[-1] - slacks[0]
            print(f"  Initial worst slack: {slacks[0]:.4f} ns")
            print(f"  Final worst slack: {slacks[-1]:.4f} ns")
            print(f"  Change: {slack_change:+.4f} ns")
            if slack_change > 0:
                print("  ✓ Timing improved")
            else:
                print("  ✗ Timing degraded")
 
    except Exception as e:
        print(f"Error analyzing trends: {e}")

    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 01_compare_stages.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Comparing Design Stages")
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
 
        compare_stages_for_flow(dataset, flow_id)
        analyze_trends(dataset, flow_id)

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
