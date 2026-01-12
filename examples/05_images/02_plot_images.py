#!/usr/bin/env python3
"""
Example: Plotting Images

Description: Demonstrates plotting and saving Image2D objects.

Prerequisites:
- EDA-schema installed
- NumPy
- Matplotlib (for plotting)

Key Concepts:
- Image plotting
- Saving images
- Colormaps
- Binary vs heatmap visualization

Usage:
    python examples/05_images/02_plot_images.py [output_dir]
"""

import sys
from pathlib import Path
import numpy as np

from eda_schema.base import Image2D


def plot_binary_image(output_dir: Path):
    """Plot a binary (mask) image."""
    print("=" * 60)
    print("Plotting Binary Image")
    print("=" * 60)

    # Create binary placement mask
    placement = np.zeros((100, 100), dtype=np.uint8)
    np.random.seed(42)
    for _ in range(200):
        x = np.random.randint(0, 100)
        y = np.random.randint(0, 100)
        placement[y, x] = 1

    image = Image2D(placement)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Plot normal
    output_path = output_dir / "placement_normal.png"
    image.plot(str(output_path), invert_mask=False)
    print(f"Saved: {output_path}")

    # Plot inverted
    output_path = output_dir / "placement_inverted.png"
    image.plot(str(output_path), invert_mask=True)
    print(f"Saved: {output_path}")

    print()


def plot_heatmap_image(output_dir: Path):
    """Plot a heatmap image."""
    print("=" * 60)
    print("Plotting Heatmap Image")
    print("=" * 60)

    # Create routing density heatmap
    density = np.random.rand(100, 100).astype(np.float32) * 10.0
    image = Image2D(density)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Plot with different colormaps
    colormaps = ['gray', 'hot', 'viridis', 'plasma']

    for cmap in colormaps:
        output_path = output_dir / f"routing_{cmap}.png"
        image.plot(str(output_path), cmap=cmap)
        print(f"Saved: {output_path} ({cmap} colormap)")

    print()


def plot_multiple_images(output_dir: Path):
    """Plot multiple images."""
    print("=" * 60)
    print("Plotting Multiple Images")
    print("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Create different images
    images = {
        'placement': Image2D(np.random.randint(0, 2, (50, 50), dtype=np.uint8)),
        'routing_density': Image2D(np.random.rand(50, 50).astype(np.float32) * 5.0),
        'metal_m1': Image2D(np.random.rand(50, 50).astype(np.float32) * 3.0),
    }

    for name, image in images.items():
        output_path = output_dir / f"{name}.png"
        image.plot(str(output_path))
        print(f"Saved: {output_path}")

    print()


def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("EDA-Schema: Plotting Images")
    print("=" * 60 + "\n")

    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("img_output")
    print(f"Output directory: {output_dir}\n")

    # Plot different types of images
    plot_binary_image(output_dir)
    plot_heatmap_image(output_dir)
    plot_multiple_images(output_dir)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print(f"\nImages saved to: {output_dir}")
    print()


if __name__ == "__main__":
    main()
