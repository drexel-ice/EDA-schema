#!/usr/bin/env python3
"""
Example: Power Analysis

Description: Demonstrates analyzing power metrics and breakdowns.

Prerequisites:
- EDA-schema installed
- A dataset with power metrics

Key Concepts:
- Power breakdown analysis
- Power component analysis
- Power trends
- Power optimization insights

Usage:
    python examples/06_analysis/02_power_analysis.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def analyze_power_breakdown(dataset: Dataset, flow_id: str, stage: str):
    """Analyze power breakdown."""
    print("=" * 60)
    print(f"Power Breakdown: {flow_id}/{stage}")
    print("=" * 60)

    try:
        power = dataset.db.get_entity('power_metrics', flow_id=flow_id, stage=stage)
 
        total = power.total_power
 
        print(f"Total Power: {total:.4f} W\n")
        print("Component Breakdown:")
        print(f"  Combinational: {power.combinational_power:.4f} W "
              f"({100*power.combinational_power/total:.1f}%)")
        print(f"  Sequential: {power.sequential_power:.4f} W "
              f"({100*power.sequential_power/total:.1f}%)")
        print(f"  Macro: {power.macro_power:.4f} W "
              f"({100*power.macro_power/total:.1f}%)")
        print(f"\nPower Types:")
        print(f"  Internal: {power.internal_power:.4f} W "
              f"({100*power.internal_power/total:.1f}%)")
        print(f"  Switching: {power.switching_power:.4f} W "
              f"({100*power.switching_power/total:.1f}%)")
        print(f"  Leakage: {power.leakage_power:.4f} W "
              f"({100*power.leakage_power/total:.1f}%)")
 
        print()

    except Exception as e:
        print(f"Error analyzing power: {e}")


def compare_power_across_stages(dataset: Dataset, flow_id: str):
    """Compare power across design stages."""
    print("=" * 60)
    print("Power Comparison Across Stages")
    print("=" * 60)

    try:
        stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
 
        if stages_df.empty:
            print("No stages available")
            return
 
        stages = stages_df['stage'].tolist()
 
        print(f"{'Stage':<20} {'Total (W)':<15} {'Combinational (W)':<20} {'Sequential (W)':<20} {'Leakage (W)':<15}")
        print("-" * 90)
 
        for stage in stages:
            try:
                power = dataset.db.get_entity('power_metrics',
                                             flow_id=flow_id,
                                             stage=stage)
                print(f"{stage:<20} {power.total_power:<15.4f} "
                      f"{power.combinational_power:<20.4f} "
                      f"{power.sequential_power:<20.4f} "
                      f"{power.leakage_power:<15.4f}")
            except:
                print(f"{stage:<20} {'N/A':<15} {'N/A':<20} {'N/A':<20} {'N/A':<15}")
 
        print()

    except Exception as e:
        print(f"Error comparing power: {e}")


def analyze_power_efficiency(dataset: Dataset, flow_id: str, stage: str):
    """Analyze power efficiency."""
    print("=" * 60)
    print("Power Efficiency Analysis")
    print("=" * 60)

    try:
        power = dataset.db.get_entity('power_metrics', flow_id=flow_id, stage=stage)
        area = dataset.db.get_entity('area_metrics', flow_id=flow_id, stage=stage)
        cell_metrics = dataset.db.get_entity('cell_metrics', flow_id=flow_id, stage=stage)
 
        total_power = power.total_power
        total_area = area.total_area
        total_cells = cell_metrics.no_of_total_cells
 
        if total_area > 0:
            power_density = total_power / total_area
            print(f"Power Density: {power_density:.6f} W/um²")
 
        if total_cells > 0:
            power_per_cell = total_power / total_cells
            print(f"Power per Cell: {power_per_cell:.6f} W/cell")
 
        # Analyze power breakdown efficiency
        if power.total_power > 0:
            dynamic_power = power.internal_power + power.switching_power
            dynamic_ratio = dynamic_power / power.total_power
            leakage_ratio = power.leakage_power / power.total_power
 
            print(f"\nPower Composition:")
            print(f"  Dynamic: {dynamic_power:.4f} W ({100*dynamic_ratio:.1f}%)")
            print(f"  Leakage: {power.leakage_power:.4f} W ({100*leakage_ratio:.1f}%)")
 
        print()

    except Exception as e:
        print(f"Error analyzing efficiency: {e}")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 02_power_analysis.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Power Analysis")
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
 
        analyze_power_breakdown(dataset, flow_id, stage)
        compare_power_across_stages(dataset, flow_id)
        analyze_power_efficiency(dataset, flow_id, stage)

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
