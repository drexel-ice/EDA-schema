#!/usr/bin/env python3
"""
Example: Load and Inspect Dataset

Description: Demonstrates advanced dataset loading and inspection techniques,
including loading specific flows, stages, and analyzing dataset structure.

Prerequisites:
- EDA-schema installed
- A dataset directory

Key Concepts:
- Loading strategies
- Dataset structure inspection
- Flow and stage navigation
- Entity access patterns

Usage:
    python examples/03_datasets/01_load_and_inspect.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def load_complete_dataset(dataset_path: str):
    """Load complete dataset."""
    print("=" * 60)
    print("Loading Complete Dataset")
    print("=" * 60)

    db = ParquetDB(dataset_path)
    dataset = Dataset(db)
    dataset.load_standard_cells()

    # Load all flows
    dataset.load()

    print(f"Loaded {len(dataset)} design flow(s)")
    for flow_id in dataset.keys():
        print(f"  - {flow_id}")
    print()

    return dataset


def inspect_flow_structure(dataset: Dataset, flow_id: str):
    """Inspect structure of a design flow."""
    print("=" * 60)
    print(f"Inspecting Flow: {flow_id}")
    print("=" * 60)

    if flow_id not in dataset:
        print(f"Flow {flow_id} not found")
        return

    design_flow = dataset[flow_id]
    print(f"Design: {design_flow.design}")
    print(f"Run status: {design_flow.run_status}")
    print(f"Stages: {len(design_flow.stages)}")

    for stage_name, design_stage in design_flow.stages.items():
        print(f"\n  Stage: {stage_name}")
        print(f"    Run status: {design_stage.run_status}")

        if design_stage.netlist:
            netlist = design_stage.netlist
            print(f"    Netlist: {netlist.no_of_cells} cells, {netlist.no_of_nets} nets")

        if design_stage.cell_metrics:
            print(f"    Cells: {design_stage.cell_metrics.no_of_total_cells} total")

        if design_stage.power_metrics:
            print(f"    Power: {design_stage.power_metrics.total_power:.4f} W")

        if design_stage.area_metrics:
            print(f"    Area: {design_stage.area_metrics.total_area:.2f} um²")

    print()


def load_specific_stage(dataset: Dataset, flow_id: str, stage: str):
    """Load and inspect a specific design stage."""
    print("=" * 60)
    print(f"Loading Stage: {flow_id}/{stage}")
    print("=" * 60)

    try:
        design_stage = dataset.load_design_stage(flow_id, stage)

        print("Design Stage Information:")
        print(f"  Flow ID: {flow_id}")
        print(f"  Stage: {stage}")
        print(f"  Run status: {design_stage.run_status}")

        if design_stage.netlist:
            netlist = design_stage.netlist
            print(f"\nNetlist:")
            print(f"  Cells: {netlist.no_of_cells}")
            print(f"  Nets: {netlist.no_of_nets}")
            print(f"  Pins: {netlist.no_of_pins}")
            print(f"  Utilization: {netlist.utilization:.2%}")
            if netlist.width and netlist.height:
                print(f"  Size: {netlist.width} x {netlist.height}")

        if design_stage.cell_metrics:
            print(f"\nCell Metrics:")
            print(f"  Total: {design_stage.cell_metrics.no_of_total_cells}")
            print(f"  Combinational: {design_stage.cell_metrics.no_of_combinational_cells}")
            print(f"  Sequential: {design_stage.cell_metrics.no_of_sequential_cells}")

        if design_stage.power_metrics:
            print(f"\nPower Metrics:")
            print(f"  Total: {design_stage.power_metrics.total_power:.4f} W")
            print(f"  Combinational: {design_stage.power_metrics.combinational_power:.4f} W")
            print(f"  Sequential: {design_stage.power_metrics.sequential_power:.4f} W")

        if design_stage.area_metrics:
            print(f"\nArea Metrics:")
            print(f"  Total: {design_stage.area_metrics.total_area:.2f} um²")
            print(f"  Cell area: {design_stage.area_metrics.cell_area:.2f} um²")

        if design_stage.timing_metrics:
            print(f"\nTiming Metrics:")
            print(f"  Worst slack: {design_stage.timing_metrics.worst_slack:.4f} ns")
            print(f"  Violating endpoints: {design_stage.timing_metrics.no_of_violating_endpoints}")

    except Exception as e:
        print(f"Error loading stage: {e}")

    print()


def analyze_dataset_statistics(dataset: Dataset):
    """Analyze overall dataset statistics."""
    print("=" * 60)
    print("Dataset Statistics")
    print("=" * 60)

    total_flows = len(dataset)
    total_stages = 0
    total_cells = 0
    total_nets = 0

    for flow_id, design_flow in dataset.items():
        total_stages += len(design_flow.stages)
        for stage_name, design_stage in design_flow.stages.items():
            if design_stage.netlist:
                total_cells += design_stage.netlist.no_of_cells
                total_nets += design_stage.netlist.no_of_nets

    print(f"Total flows: {total_flows}")
    print(f"Total stages: {total_stages}")
    print(f"Total cells: {total_cells}")
    print(f"Total nets: {total_nets}")
    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 02_load_and_inspect.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Loading and Inspecting Dataset")
    print("=" * 60 + "\n")

    # Load dataset
    dataset = load_complete_dataset(str(dataset_path))

    # Inspect first flow
    if dataset:
        first_flow_id = list(dataset.keys())[0]
        inspect_flow_structure(dataset, first_flow_id)

        # Load specific stage
        design_flow = dataset[first_flow_id]
        if design_flow.stages:
            first_stage = list(design_flow.stages.keys())[0]
            load_specific_stage(dataset, first_flow_id, first_stage)

    # Analyze statistics
    analyze_dataset_statistics(dataset)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
