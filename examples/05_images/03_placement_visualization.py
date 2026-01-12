#!/usr/bin/env python3
"""
Example: Placement Visualization

Description:
Demonstrates creating and visualizing cell placement images
from netlist data.

Prerequisites:
- EDA-schema installed
- A dataset with gate placement data

Key Concepts:
- Creating placement images from gates
- Visualizing cell locations
- Placement density analysis

Usage:
    python examples/05_images/03_placement_visualization.py [dataset_path] [output_dir]
"""

import sys
from pathlib import Path
import numpy as np

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB
from eda_schema.base import Image2D


COORD_COLS = ("x_min", "y_min", "x_max", "y_max")


def valid_gate_coords(gate) -> bool:
    """Return True if gate has all required finite placement coordinates."""
    if not all(c in gate for c in COORD_COLS):
        return False
    return not any(np.isnan(gate[c]) for c in COORD_COLS)


def create_placement_from_gates(
    dataset: Dataset,
    flow_id: str,
    stage: str,
    resolution: int = 100,
):
    """Create placement image from gate positions."""
    print("=" * 60)
    print("Creating Placement Image from Gates")
    print("=" * 60)

    try:
        gates_df = dataset.db.get_table_data(
            "gates", flow_id=flow_id, stage=stage
        )

        if gates_df.empty:
            print("No gates available")
            return None

        try:
            netlist = dataset.db.get_entity(
                "netlists", flow_id=flow_id, stage=stage
            )
            width = netlist.width or 100.0
            height = netlist.height or 100.0
        except Exception:
            width = (
                gates_df["x_max"].max()
                if "x_max" in gates_df.columns
                else 100.0
            )
            height = (
                gates_df["y_max"].max()
                if "y_max" in gates_df.columns
                else 100.0
            )

        placement = np.zeros((resolution, resolution), dtype=np.uint8)

        scale_x = resolution / width if width > 0 else 1.0
        scale_y = resolution / height if height > 0 else 1.0

        placed_count = 0
        skipped_count = 0

        for _, gate in gates_df.iterrows():
            if not valid_gate_coords(gate):
                skipped_count += 1
                continue

            x_min = int(gate["x_min"] * scale_x)
            y_min = int(gate["y_min"] * scale_y)
            x_max = int(gate["x_max"] * scale_x)
            y_max = int(gate["y_max"] * scale_y)

            x_min = max(0, min(x_min, resolution - 1))
            y_min = max(0, min(y_min, resolution - 1))
            x_max = max(0, min(x_max, resolution - 1))
            y_max = max(0, min(y_max, resolution - 1))

            placement[y_min : y_max + 1, x_min : x_max + 1] = 1
            placed_count += 1

        image = Image2D(placement)

        print(f"Created placement image: {image.shape}")
        print(f"  Design size: {width} x {height}")
        print(f"  Image resolution: {resolution} x {resolution}")
        print(f"  Placed gates: {placed_count}")
        print(f"  Skipped gates (no placement): {skipped_count}")
        print(f"  Placement density: {np.sum(placement) / placement.size:.2%}")
        print()

        return image

    except Exception as e:
        print(f"Error creating placement image: {e}")
        import traceback

        traceback.print_exc()
        return None


def create_placement_by_type(
    dataset: Dataset,
    flow_id: str,
    stage: str,
    resolution: int = 100,
):
    """Create separate placement images for different cell types."""
    print("=" * 60)
    print("Creating Placement Images by Cell Type")
    print("=" * 60)

    try:
        gates_df = dataset.db.get_table_data(
            "gates", flow_id=flow_id, stage=stage
        )

        if gates_df.empty:
            print("No gates available")
            return {}

        if "standard_cell" not in gates_df.columns:
            print("No standard_cell column found")
            return {}

        try:
            netlist = dataset.db.get_entity(
                "netlists", flow_id=flow_id, stage=stage
            )
            width = netlist.width or 100.0
            height = netlist.height or 100.0
        except Exception:
            width = (
                gates_df["x_max"].max()
                if "x_max" in gates_df.columns
                else 100.0
            )
            height = (
                gates_df["y_max"].max()
                if "y_max" in gates_df.columns
                else 100.0
            )

        scale_x = resolution / width if width > 0 else 1.0
        scale_y = resolution / height if height > 0 else 1.0

        images = {}
        cell_types = gates_df["standard_cell"].unique()
        print(f"Found {len(cell_types)} cell types")

        for cell_type in cell_types[:5]:
            placement = np.zeros((resolution, resolution), dtype=np.uint8)
            cell_gates = gates_df[gates_df["standard_cell"] == cell_type]

            placed = 0
            skipped = 0

            for _, gate in cell_gates.iterrows():
                if not valid_gate_coords(gate):
                    skipped += 1
                    continue

                x_min = int(gate["x_min"] * scale_x)
                y_min = int(gate["y_min"] * scale_y)
                x_max = int(gate["x_max"] * scale_x)
                y_max = int(gate["y_max"] * scale_y)

                x_min = max(0, min(x_min, resolution - 1))
                y_min = max(0, min(y_min, resolution - 1))
                x_max = max(0, min(x_max, resolution - 1))
                y_max = max(0, min(y_max, resolution - 1))

                placement[y_min : y_max + 1, x_min : x_max + 1] = 1
                placed += 1

            images[cell_type] = Image2D(placement)
            print(
                f"  {cell_type}: placed={placed}, skipped={skipped}"
            )

        return images

    except Exception as e:
        print(f"Error creating placement-by-type images: {e}")
        return {}


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = Path(sys.argv[1])
    else:
        dataset_path = (
            Path(__file__).parent.parent.parent / "dataset" / "test"
        )
        if not dataset_path.exists():
            print(
                "Usage: python 03_placement_visualization.py <dataset_path> [output_dir]"
            )
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    output_dir = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else Path("placement_output")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("EDA-Schema: Placement Visualization")
    print("=" * 60)
    print()

    db = ParquetDB(str(dataset_path))
    dataset = Dataset(db)
    dataset.load_standard_cells()

    try:
        flows_df = dataset.db.get_table_data("design_flows")
        if flows_df.empty:
            print("No flows available")
            return

        flow_id = flows_df.iloc[0]["flow_id"]
        stages_df = dataset.db.get_table_data(
            "design_stages", flow_id=flow_id
        )

        if stages_df.empty:
            print("No stages available")
            return

        stage = stages_df.iloc[0]["stage"]

        placement_image = create_placement_from_gates(
            dataset, flow_id, stage
        )

        if placement_image is not None:
            output_path = output_dir / "placement.png"
            placement_image.plot(
                str(output_path), invert_mask=True
            )
            print(f"Saved placement image: {output_path}")

        type_images = create_placement_by_type(
            dataset, flow_id, stage
        )

        for cell_type, image in type_images.items():
            safe_name = cell_type.replace("/", "_")
            output_path = output_dir / f"placement_{safe_name}.png"
            image.plot(str(output_path), invert_mask=True)
            print(f"Saved {cell_type} placement: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print(f"\nImages saved to: {output_dir}")
    print()


if __name__ == "__main__":
    main()
