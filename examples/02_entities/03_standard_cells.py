#!/usr/bin/env python3
"""
Example: Working with Standard Cells

Description: Demonstrates creating and managing standard cell libraries.

Prerequisites:
- EDA-schema installed

Key Concepts:
- Standard cell entities
- Standard cell library management
- Using standard cells in gates

Usage:
    python examples/02_entities/03_standard_cells.py
"""

from eda_schema import entity
from eda_schema.dataset import Dataset, StandardCellData


def create_standard_cells():
    """Create a collection of standard cells."""
    print("=" * 60)
    print("Creating Standard Cells")
    print("=" * 60)

    cells = []

    # NAND2 gate
    nand2 = entity.StandardCellEntity(
        name='NAND2_X1',
        width=0.5,
        height=2.0,
        no_of_input_pins=2,
        no_of_output_pins=1,
        is_sequential=False,
        is_inverter=False,
        is_buffer=False,
        is_filler=False,
        is_diode=False
    )
    cells.append(nand2)
    print(f"  {nand2.name}: {nand2.width}x{nand2.height}, {nand2.no_of_input_pins} inputs")

    # Inverter
    inv = entity.StandardCellEntity(
        name='INV_X1',
        width=0.5,
        height=2.0,
        no_of_input_pins=1,
        no_of_output_pins=1,
        is_sequential=False,
        is_inverter=True,
        is_buffer=False,
        is_filler=False,
        is_diode=False
    )
    cells.append(inv)
    print(f"  {inv.name}: inverter, {inv.width}x{inv.height}")

    # Buffer
    buf = entity.StandardCellEntity(
        name='BUF_X1',
        width=0.5,
        height=2.0,
        no_of_input_pins=1,
        no_of_output_pins=1,
        is_sequential=False,
        is_inverter=False,
        is_buffer=True,
        is_filler=False,
        is_diode=False
    )
    cells.append(buf)
    print(f"  {buf.name}: buffer, {buf.width}x{buf.height}")

    # D Flip-Flop (sequential)
    dff = entity.StandardCellEntity(
        name='DFF_X1',
        width=1.0,
        height=2.0,
        no_of_input_pins=2,  # D, CLK
        no_of_output_pins=1,  # Q
        is_sequential=True,
        is_inverter=False,
        is_buffer=False,
        is_filler=False,
        is_diode=False
    )
    cells.append(dff)
    print(f"  {dff.name}: sequential, {dff.width}x{dff.height}")

    print(f"\nCreated {len(cells)} standard cells")
    print()

    return cells


def use_standard_cells_in_gates(standard_cells):
    """Demonstrate using standard cells in gates."""
    print("=" * 60)
    print("Using Standard Cells in Gates")
    print("=" * 60)

    # Create gates using standard cells
    gates = []

    for i, std_cell in enumerate(standard_cells[:3]):  # Use first 3
        gate = entity.GateEntity(
            flow_id='example_flow',
            stage='floorplan',
            name=f'U{i+1}',
            standard_cell=std_cell.name,
            x_min=10.0 + i * 20.0,
            y_min=10.0,
            x_max=10.0 + i * 20.0 + std_cell.width,
            y_max=10.0 + std_cell.height,
            no_of_inputs=std_cell.no_of_input_pins,
            no_of_outputs=std_cell.no_of_output_pins
        )
        gates.append(gate)
        print(f"  Gate {gate.name}: uses {gate.standard_cell}")
        print(f"    Size: {gate.x_max - gate.x_min} x {gate.y_max - gate.y_min}")
        print(f"    I/O: {gate.no_of_inputs} inputs, {gate.no_of_outputs} outputs")

    print()
    return gates


def manage_standard_cell_library():
    """Demonstrate managing a standard cell library."""
    print("=" * 60)
    print("Managing Standard Cell Library")
    print("=" * 60)

    # Create StandardCellData container
    std_cell_data = StandardCellData()

    # Add cells
    cells = create_standard_cells()
    for cell in cells:
        std_cell_data.add_cell(cell)

    print(f"Library contains {len(std_cell_data)} cells")
    print(f"Sequential cells: {len(std_cell_data.seq_cells)}")
    print(f"  {std_cell_data.seq_cells}")
    print()

    # Access cells
    print("Accessing cells:")
    for cell_name in ['NAND2_X1', 'INV_X1', 'DFF_X1']:
        if cell_name in std_cell_data:
            cell = std_cell_data[cell_name]
            print(f"  {cell_name}: {cell.width}x{cell.height}")
    print()

    return std_cell_data


def main():
    """Run all standard cell examples."""
    print("\n" + "=" * 60)
    print("EDA-Schema: Working with Standard Cells")
    print("=" * 60 + "\n")

    # Create standard cells
    standard_cells = create_standard_cells()

    # Use in gates
    gates = use_standard_cells_in_gates(standard_cells)

    # Manage library
    library = manage_standard_cell_library()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try examples/03_datasets/ to work with datasets")
    print("  - Try 04_metrics_entities.py for metrics")
    print()


if __name__ == "__main__":
    main()
