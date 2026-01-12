#!/usr/bin/env python3
"""
Example: Creating Images

Description: Demonstrates creating Image2D objects for placement and routing
visualizations.

Prerequisites:
- EDA-schema installed
- NumPy

Key Concepts:
- Image2D creation
- Placement images
- Routing images
- Image validation

Usage:
    python examples/05_images/01_create_images.py

See Also:
    - Interactive Notebook: notebooks/tutorials/05_image_visualization.ipynb
    - User Guide: docs/guides/user_guide.md#image-data
    - How-To: docs/howto/work_with_images.md
"""

import numpy as np
from eda_schema.base import Image2D


def create_placement_image():
    """Create a placement image."""
    print("=" * 60)
    print("Creating Placement Image")
    print("=" * 60)

    # Create binary placement mask
    width, height = 100, 100
    placement = np.zeros((height, width), dtype=np.uint8)

    # Place some cells (random for demo)
    np.random.seed(42)
    for _ in range(50):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        placement[y, x] = 1

    image = Image2D(placement)
    print(f"Created placement image: {image.shape}")
    print(f"  Unique values: {np.unique(image)}")
    print(f"  Placed cells: {np.sum(image == 1)}")

    # Validate
    image.validate()
    print("  Image validated successfully")
    print()

    return image


def create_routing_density_image():
    """Create a routing density heatmap."""
    print("=" * 60)
    print("Creating Routing Density Image")
    print("=" * 60)

    # Create routing density (float values)
    width, height = 100, 100
    density = np.random.rand(height, width).astype(np.float32) * 10.0

    image = Image2D(density)
    print(f"Created routing density image: {image.shape}")
    print(f"  Min density: {np.min(image):.2f}")
    print(f"  Max density: {np.max(image):.2f}")
    print(f"  Mean density: {np.mean(image):.2f}")

    # Validate
    image.validate()
    print("  Image validated successfully")
    print()

    return image


def create_metal_layer_images():
    """Create images for different metal layers."""
    print("=" * 60)
    print("Creating Metal Layer Images")
    print("=" * 60)

    metal_layers = {}
    width, height = 100, 100

    for layer in ['M1', 'M2', 'M3']:
        # Create routing for this layer
        routing = np.random.rand(height, width).astype(np.float32) * 5.0
        metal_layers[layer] = Image2D(routing)
        print(f"  {layer}: {metal_layers[layer].shape}, "
              f"max={np.max(metal_layers[layer]):.2f}")

    print()
    return metal_layers


def demonstrate_image_operations():
    """Demonstrate image operations."""
    print("=" * 60)
    print("Image Operations")
    print("=" * 60)

    # Create image
    image = Image2D(np.random.rand(50, 50).astype(np.float32))

    # Get as numpy array
    array = np.array(image)
    print(f"Image shape: {image.shape}")
    print(f"Array shape: {array.shape}")
    print(f"Are equal: {np.array_equal(image, array)}")

    # Image properties
    print(f"\nImage properties:")
    print(f"  Min: {np.min(image):.4f}")
    print(f"  Max: {np.max(image):.4f}")
    print(f"  Mean: {np.mean(image):.4f}")
    print(f"  Unique values: {len(np.unique(image))}")

    print()


def main():
    """Run all image creation examples."""
    print("\n" + "=" * 60)
    print("EDA-Schema: Creating Images")
    print("=" * 60 + "\n")

    # Create different types of images
    placement_image = create_placement_image()
    routing_image = create_routing_density_image()
    metal_layers = create_metal_layer_images()

    # Demonstrate operations
    demonstrate_image_operations()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try 02_plot_images.py to visualize images")
    print("  - Try 03_placement_visualization.py for placement")
    print()


if __name__ == "__main__":
    main()
