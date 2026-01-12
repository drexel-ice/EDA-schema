#!/usr/bin/env python3
"""
Example: Routing Visualization

Description: Demonstrates creating and visualizing routing images.

Prerequisites:
- EDA-schema installed
- A dataset with routing/net data

Key Concepts:
- Routing density visualization
- Metal layer visualization
- Routing congestion analysis

Usage:
    python examples/05_images/04_routing_visualization.py [dataset_path] [output_dir]
"""

import sys
from pathlib import Path
import numpy as np

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB
from eda_schema.base import Image2D


def create_routing_density_from_nets(dataset: Dataset, flow_id: str, stage: str,
                                     resolution: int = 100):
    """Create routing density image from net data."""
    print("=" * 60)
    print("Creating Routing Density from Nets")
    print("=" * 60)

    try:
        # Get nets
        nets_df = dataset.db.get_table_data('nets', flow_id=flow_id, stage=stage)
 
        if nets_df.empty:
            print("No nets available")
            return None
 
        # Get dimensions
        try:
            netlist = dataset.db.get_entity('netlists', flow_id=flow_id, stage=stage)
            width = netlist.width or 100.0
            height = netlist.height or 100.0
        except:
            if all(col in nets_df.columns for col in ['x_min', 'y_min', 'x_max', 'y_max']):
                width = nets_df['x_max'].max() if not nets_df.empty else 100.0
                height = nets_df['y_max'].max() if not nets_df.empty else 100.0
            else:
                width = height = 100.0
 
        # Create routing density image
        density = np.zeros((resolution, resolution), dtype=np.float32)
 
        scale_x = resolution / width if width > 0 else 1.0
        scale_y = resolution / height if height > 0 else 1.0
 
        # Add routing density from nets
        for _, net in nets_df.iterrows():
            if all(col in net for col in ['x_min', 'y_min', 'x_max', 'y_max']):
                x_min = max(0, min(int(net['x_min'] * scale_x), resolution - 1))
                y_min = max(0, min(int(net['y_min'] * scale_y), resolution - 1))
                x_max = max(0, min(int(net['x_max'] * scale_x), resolution - 1))
                y_max = max(0, min(int(net['y_max'] * scale_y), resolution - 1))
 
                # Add density based on net length or fanout
                net_weight = net.get('no_of_fanouts', 1) if 'no_of_fanouts' in net else 1
                density[y_min:y_max+1, x_min:x_max+1] += net_weight
 
        image = Image2D(density)
        print(f"Created routing density image: {image.shape}")
        print(f"  Design size: {width} x {height}")
        print(f"  Image resolution: {resolution} x {resolution}")
        print(f"  Min density: {np.min(image):.2f}")
        print(f"  Max density: {np.max(image):.2f}")
        print(f"  Mean density: {np.mean(image):.2f}")
        print()
 
        return image

    except Exception as e:
        print(f"Error creating routing density: {e}")
        import traceback
        traceback.print_exc()
        return None


def visualize_netlist_routing(netlist):
    """Visualize routing from netlist if available."""
    print("=" * 60)
    print("Visualizing Netlist Routing")
    print("=" * 60)

    images = {}

    # Check for routing images in netlist
    if netlist.routing:
        images['routing'] = netlist.routing
        print("Found routing image in netlist")

    # Check for metal layer routing
    if netlist.routing_by_metal:
        for layer, routing_image in netlist.routing_by_metal.items():
            images[f'routing_{layer}'] = routing_image
            print(f"Found routing image for {layer}")

    if not images:
        print("No routing images found in netlist")

    print()
    return images


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 04_routing_visualization.py <dataset_path> [output_dir]")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("routing_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("EDA-Schema: Routing Visualization")
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
 
        # Create routing density from nets
        routing_image = create_routing_density_from_nets(dataset, flow_id, stage)
 
        if routing_image:
            output_path = output_dir / "routing_density.png"
            routing_image.plot(str(output_path), cmap='hot')
            print(f"Saved routing density: {output_path}")
 
        # Try to get routing from netlist
        try:
            netlist = dataset.load_netlist(flow_id, stage)
            netlist_images = visualize_netlist_routing(netlist)
 
            for name, image in netlist_images.items():
                output_path = output_dir / f"{name}.png"
                if len(np.unique(image)) <= 2:
                    image.plot(str(output_path))
                else:
                    image.plot(str(output_path), cmap='hot')
                print(f"Saved {name}: {output_path}")
        except:
            pass

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print(f"\nImages saved to: {output_dir}")
    print()


if __name__ == "__main__":
    main()
