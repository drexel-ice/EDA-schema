#!/usr/bin/env python3
"""
Example: Create Basic Entities

Description: Demonstrates how to create basic tabular entities including
gates, ports, pins, and nets.

Prerequisites:
- EDA-schema installed
- Basic understanding of Python dataclasses

Key Concepts:
- Entity creation
- Required vs optional fields
- Entity validation

Usage:
    python examples/01_basics/01_create_entities.py

Output:
    Creates and displays various entity types with their properties.

See Also:
    - Tutorial: tutorials/01_getting_started/
    - Notebook: notebooks/tutorials/01_getting_started.ipynb
    - User Guide: docs/guides/user_guide.md#working-with-entities
"""

from eda_schema import entity


def create_gate_entity():
    """Create a GateEntity representing a logic gate."""
    print("=" * 60)
    print("Creating GateEntity")
    print("=" * 60)

    gate = entity.GateEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='gate_001',
        standard_cell='NAND2_X1',
        x_min=10.0,
        y_min=20.0,
        x_max=15.0,
        y_max=25.0,
        no_of_inputs=2,
        no_of_outputs=1
    )

    print(f"Created gate: {gate.name}")
    print(f"  Standard cell: {gate.standard_cell}")
    print(f"  Position: ({gate.x_min}, {gate.y_min}) to ({gate.x_max}, {gate.y_max})")
    print(f"  Inputs: {gate.no_of_inputs}, Outputs: {gate.no_of_outputs}")
    print()

    return gate


def create_port_entity():
    """Create a PortEntity representing an I/O port."""
    print("=" * 60)
    print("Creating PortEntity")
    print("=" * 60)

    port = entity.PortEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='clk',
        direction='INPUT',
        x=0.0,
        y=0.0
    )

    print(f"Created port: {port.name}")
    print(f"  Direction: {port.direction}")
    print(f"  Position: ({port.x}, {port.y})")
    print()

    return port


def create_pin_entity():
    """Create a PinEntity representing a pin on a gate."""
    print("=" * 60)
    print("Creating PinEntity")
    print("=" * 60)

    pin = entity.PinEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='gate_001/A',
        direction='INPUT',
        is_startpoint=True,
        is_endpoint=False,
        x_min=10.0,
        y_min=20.0,
        x_max=12.0,
        y_max=22.0
    )

    print(f"Created pin: {pin.name}")
    print(f"  Direction: {pin.direction}")
    print(f"  Is startpoint: {pin.is_startpoint}")
    print(f"  Is endpoint: {pin.is_endpoint}")
    print(f"  Position: ({pin.x_min}, {pin.y_min}) to ({pin.x_max}, {pin.y_max})")
    print()

    return pin


def create_net_entity():
    """Create a NetEntity representing a wire/net."""
    print("=" * 60)
    print("Creating NetEntity")
    print("=" * 60)

    net = entity.NetEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='net_001',
        is_special_net=False,
        no_of_fanouts=3,
        x_min=0.0,
        y_min=0.0,
        x_max=100.0,
        y_max=100.0,
        length=150.0
    )

    print(f"Created net: {net.name}")
    print(f"  Special net: {net.is_special_net}")
    print(f"  Fanouts: {net.no_of_fanouts}")
    print(f"  Bounding box: ({net.x_min}, {net.y_min}) to ({net.x_max}, {net.y_max})")
    print(f"  Length: {net.length}")
    print()

    return net


def create_metrics_entities():
    """Create metrics entities."""
    print("=" * 60)
    print("Creating Metrics Entities")
    print("=" * 60)

    # Power metrics
    power_metrics = entity.PowerMetricsEntity(
        flow_id='example_flow',
        stage='floorplan',
        combinational_power=0.1,
        sequential_power=0.2,
        macro_power=0.05,
        internal_power=0.08,
        switching_power=0.07,
        leakage_power=0.01,
        total_power=0.51
    )

    print("Power Metrics:")
    print(f"  Total power: {power_metrics.total_power} W")
    print(f"  Combinational: {power_metrics.combinational_power} W")
    print(f"  Sequential: {power_metrics.sequential_power} W")
    print()

    # Area metrics
    area_metrics = entity.AreaMetricsEntity(
        flow_id='example_flow',
        stage='floorplan',
        combinational_cell_area=100.0,
        sequential_cell_area=50.0,
        buffer_area=10.0,
        inverter_area=5.0,
        filler_area=0.0,
        tap_cell_area=0.0,
        diode_area=0.0,
        macro_area=0.0,
        cell_area=165.0,
        total_area=200.0
    )

    print("Area Metrics:")
    print(f"  Total area: {area_metrics.total_area} um²")
    print(f"  Cell area: {area_metrics.cell_area} um²")
    print(f"  Combinational: {area_metrics.combinational_cell_area} um²")
    print()

    return power_metrics, area_metrics


def get_tabular_data_demo():
    """Demonstrate getting tabular data from entities."""
    print("=" * 60)
    print("Getting Tabular Data")
    print("=" * 60)

    gate = entity.GateEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='gate_001',
        standard_cell='NAND2_X1',
        x_min=10.0,
        y_min=20.0,
        x_max=15.0,
        y_max=25.0,
        no_of_inputs=2,
        no_of_outputs=1
    )

    tabular_data = gate.get_tabular_data()
    print("Tabular data (for database storage):")
    for key, value in tabular_data.items():
        print(f"  {key}: {value}")
    print()


def main():
    """Run all entity creation examples."""
    print("\n" + "=" * 60)
    print("EDA-Schema: Creating Basic Entities")
    print("=" * 60 + "\n")

    # Create various entities
    gate = create_gate_entity()
    port = create_port_entity()
    pin = create_pin_entity()
    net = create_net_entity()
    power_metrics, area_metrics = create_metrics_entities()

    # Demonstrate tabular data extraction
    get_tabular_data_demo()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try example 02_load_dataset.py to load existing data")
    print("  - Try example 03_query_data.py to query entities")
    print()


if __name__ == "__main__":
    main()
