#!/usr/bin/env python3
"""
Example: Area Analysis

Description: Demonstrates analyzing area metrics and breakdowns.

Prerequisites:
- EDA-schema installed
- A dataset with area metrics

Key Concepts:
- Area breakdown analysis
- Cell area analysis
- Area efficiency
- Area trends

Usage:
    python examples/06_analysis/04_area_analysis.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def analyze_area_breakdown(dataset: Dataset, flow_id: str, stage: str):
    """Analyze area breakdown."""
    print("=" * 60)
    print(f"Area Breakdown: {flow_id}/{stage}")
    print("=" * 60)

    try:
        area = dataset.db.get_entity('area_metrics', flow_id=flow_id, stage=stage)
        cell_metrics = dataset.db.get_entity('cell_metrics', flow_id=flow_id, stage=stage)
 
        total = area.total_area
 
        print(f"Total Area: {total:.2f} um²\n")
        print("Cell Area Breakdown:")
        print(f"  Combinational: {area.combinational_cell_area:.2f} um² "
              f"({100*area.combinational_cell_area/total:.1f}%)")
        print(f"  Sequential: {area.sequential_cell_area:.2f} um² "
              f"({100*area.sequential_cell_area/total:.1f}%)")
        print(f"  Buffer: {area.buffer_area:.2f} um² "
              f"({100*area.buffer_area/total:.1f}%)")
        print(f"  Inverter: {area.inverter_area:.2f} um² "
              f"({100*area.inverter_area/total:.1f}%)")
        print(f"  Filler: {area.filler_area:.2f} um² "
              f"({100*area.filler_area/total:.1f}%)")
        print(f"  Tap Cell: {area.tap_cell_area:.2f} um² "
              f"({100*area.tap_cell_area/total:.1f}%)")
        print(f"  Diode: {area.diode_area:.2f} um² "
              f"({100*area.diode_area/total:.1f}%)")
        print(f"  Macro: {area.macro_area:.2f} um² "
              f"({100*area.macro_area/total:.1f}%)")
        print(f"\nTotal Cell Area: {area.cell_area:.2f} um² "
              f"({100*area.cell_area/total:.1f}%)")
 
        # Cell counts
        print(f"\nCell Counts:")
        print(f"  Total: {cell_metrics.no_of_total_cells}")
        print(f"  Combinational: {cell_metrics.no_of_combinational_cells}")
        print(f"  Sequential: {cell_metrics.no_of_sequential_cells}")
        print(f"  Buffers: {cell_metrics.no_of_buffers}")
        print(f"  Inverters: {cell_metrics.no_of_inverters}")
 
        print()

    except Exception as e:
        print(f"Error analyzing area: {e}")


def analyze_area_efficiency(dataset: Dataset, flow_id: str, stage: str):
    """Analyze area efficiency."""
    print("=" * 60)
    print("Area Efficiency Analysis")
    print("=" * 60)

    try:
        area = dataset.db.get_entity('area_metrics', flow_id=flow_id, stage=stage)
        cell_metrics = dataset.db.get_entity('cell_metrics', flow_id=flow_id, stage=stage)
        netlist = dataset.db.get_entity('netlists', flow_id=flow_id, stage=stage)
 
        total_area = area.total_area
        cell_area = area.cell_area
        total_cells = cell_metrics.no_of_total_cells
 
        # Utilization
        if total_area > 0:
            cell_utilization = (cell_area / total_area) * 100
            print(f"Cell Area Utilization: {cell_utilization:.2f}%")
 
        # Area per cell
        if total_cells > 0:
            area_per_cell = cell_area / total_cells
            print(f"Area per Cell: {area_per_cell:.4f} um²/cell")
 
        # Combinational vs sequential
        if cell_area > 0:
            comb_ratio = area.combinational_cell_area / cell_area
            seq_ratio = area.sequential_cell_area / cell_area
            print(f"\nCell Area Composition:")
            print(f"  Combinational: {100*comb_ratio:.1f}%")
            print(f"  Sequential: {100*seq_ratio:.1f}%")
 
        # Design dimensions
        if netlist.width and netlist.height:
            design_area = netlist.width * netlist.height
            print(f"\nDesign Dimensions:")
            print(f"  Width: {netlist.width:.2f} um")
            print(f"  Height: {netlist.height:.2f} um")
            print(f"  Design Area: {design_area:.2f} um²")
            if design_area > 0:
                utilization = (total_area / design_area) * 100
                print(f"  Utilization: {utilization:.2f}%")
 
        print()

    except Exception as e:
        print(f"Error analyzing efficiency: {e}")


def compare_area_across_stages(dataset: Dataset, flow_id: str):
    """Compare area across design stages."""
    print("=" * 60)
    print("Area Comparison Across Stages")
    print("=" * 60)

    try:
        stages_df = dataset.db.get_table_data('design_stages', flow_id=flow_id)
 
        if stages_df.empty:
            print("No stages available")
            return
 
        stages = stages_df['stage'].tolist()
 
        print(f"{'Stage':<20} {'Total (um²)':<15} {'Cell (um²)':<15} {'Combinational (um²)':<20} {'Sequential (um²)':<20}")
        print("-" * 90)
 
        for stage in stages:
            try:
                area = dataset.db.get_entity('area_metrics',
                                            flow_id=flow_id,
                                            stage=stage)
                print(f"{stage:<20} {area.total_area:<15.2f} "
                      f"{area.cell_area:<15.2f} "
                      f"{area.combinational_cell_area:<20.2f} "
                      f"{area.sequential_cell_area:<20.2f}")
            except:
                print(f"{stage:<20} {'N/A':<15} {'N/A':<15} {'N/A':<20} {'N/A':<20}")
 
        print()

    except Exception as e:
        print(f"Error comparing area: {e}")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 04_area_analysis.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Area Analysis")
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
 
        analyze_area_breakdown(dataset, flow_id, stage)
        analyze_area_efficiency(dataset, flow_id, stage)
        compare_area_across_stages(dataset, flow_id)

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
