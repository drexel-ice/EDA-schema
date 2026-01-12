#!/usr/bin/env python3
"""
Example: Working with Tabular Entities

Description: Demonstrates creating and working with tabular entities
including gates, ports, pins, and nets.

Prerequisites:
- EDA-schema installed
- Completed examples/01_basics/

Key Concepts:
- Tabular entity types
- Entity relationships
- Entity validation
- Data extraction

Usage:
    python examples/02_entities/01_tabular_entities.py

See Also:
    - Interactive Notebook: notebooks/tutorials/02_working_with_entities.ipynb
    - Tutorial: tutorials/02_working_with_entities/
    - User Guide: docs/guides/user_guide.md#working-with-entities
    - How-To: docs/howto/create_entities.md
"""

from eda_schema import entity


def create_complete_gate():
    """Create a gate with all fields."""
    print("=" * 60)
    print("Creating Complete Gate Entity")
    print("=" * 60)

    gate = entity.GateEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='U1',
        standard_cell='NAND2_X1',
        x_min=10.0,
        y_min=20.0,
        x_max=15.0,
        y_max=25.0,
        no_of_inputs=2,
        no_of_outputs=1
    )

    print(f"Gate: {gate.name}")
    print(f"  Standard cell: {gate.standard_cell}")
    print(f"  Bounding box: ({gate.x_min}, {gate.y_min}) to ({gate.x_max}, {gate.y_max})")
    print(f"  Area: {(gate.x_max - gate.x_min) * (gate.y_max - gate.y_min)} um²")
    print()

    return gate


def create_port_collection():
    """Create a collection of ports."""
    print("=" * 60)
    print("Creating Port Collection")
    print("=" * 60)

    ports = []
    port_data = [
        ('clk', 'INPUT', 0.0, 0.0),
        ('reset', 'INPUT', 0.0, 10.0),
        ('data_in', 'INPUT', 0.0, 20.0),
        ('data_out', 'OUTPUT', 100.0, 0.0),
        ('valid', 'OUTPUT', 100.0, 10.0),
    ]

    for name, direction, x, y in port_data:
        port = entity.PortEntity(
            flow_id='example_flow',
            stage='floorplan',
            name=name,
            direction=direction,
            x=x,
            y=y
        )
        ports.append(port)
        print(f"  {name}: {direction} at ({x}, {y})")

    print(f"\nCreated {len(ports)} ports")
    print()

    return ports


def create_pin_collection():
    """Create pins associated with gates."""
    print("=" * 60)
    print("Creating Pin Collection")
    print("=" * 60)

    pins = []

    # Input pins for gate U1
    for pin_name in ['U1/A', 'U1/B']:
        pin = entity.PinEntity(
            flow_id='example_flow',
            stage='floorplan',
            name=pin_name,
            direction='INPUT',
            is_startpoint=False,
            is_endpoint=False,
            x_min=10.0,
            y_min=20.0,
            x_max=12.0,
            y_max=22.0
        )
        pins.append(pin)
        print(f"  {pin_name}: {pin.direction}")

    # Output pin for gate U1
    output_pin = entity.PinEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='U1/Y',
        direction='OUTPUT',
        is_startpoint=True,
        is_endpoint=False,
        x_min=13.0,
        y_min=20.0,
        x_max=15.0,
        y_max=22.0
    )
    pins.append(output_pin)
    print(f"  {output_pin.name}: {output_pin.direction} (startpoint)")

    print(f"\nCreated {len(pins)} pins")
    print()

    return pins


def create_net_collection():
    """Create nets connecting components."""
    print("=" * 60)
    print("Creating Net Collection")
    print("=" * 60)

    nets = []

    # Clock net
    clk_net = entity.NetEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='clk_net',
        is_special_net=True,  # Clock is special
        no_of_fanouts=10,
        x_min=0.0,
        y_min=0.0,
        x_max=100.0,
        y_max=100.0,
        length=200.0
    )
    nets.append(clk_net)
    print(f"  {clk_net.name}: special net, {clk_net.no_of_fanouts} fanouts")

    # Data net
    data_net = entity.NetEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='data_net',
        is_special_net=False,
        no_of_fanouts=3,
        x_min=10.0,
        y_min=20.0,
        x_max=50.0,
        y_max=30.0,
        length=45.0
    )
    nets.append(data_net)
    print(f"  {data_net.name}: regular net, {data_net.no_of_fanouts} fanouts")

    print(f"\nCreated {len(nets)} nets")
    print()

    return nets


def demonstrate_entity_relationships():
    """Demonstrate relationships between entities."""
    print("=" * 60)
    print("Entity Relationships")
    print("=" * 60)

    # Create related entities
    gate = create_complete_gate()
    ports = create_port_collection()
    pins = create_pin_collection()
    nets = create_net_collection()

    print("Entity relationships:")
    print(f"  Gate '{gate.name}' has:")
    print(f"    - {len([p for p in pins if gate.name in p.name])} pins")
    print(f"    - Connected to {len(nets)} nets")
    print()

    print(f"  Ports connect to:")
    for port in ports:
        if port.direction == 'INPUT':
            print(f"    - {port.name} -> input nets")
        else:
            print(f"    - {port.name} <- output nets")
    print()


def extract_tabular_data():
    """Demonstrate extracting tabular data from entities."""
    print("=" * 60)
    print("Extracting Tabular Data")
    print("=" * 60)

    gate = entity.GateEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='U1',
        standard_cell='NAND2_X1',
        x_min=10.0,
        y_min=20.0,
        x_max=15.0,
        y_max=25.0,
        no_of_inputs=2,
        no_of_outputs=1
    )

    tabular = gate.get_tabular_data()

    print("Tabular data for database storage:")
    print(f"  Primary keys: flow_id={tabular['flow_id']}, stage={tabular['stage']}, name={tabular['name']}")
    print(f"  Attributes: {len([k for k in tabular.keys() if k not in ['flow_id', 'stage', 'name']])} fields")
    print()

    # Show how to prepare for batch insertion
    gates_data = [gate.get_tabular_data()]
    print(f"Prepared {len(gates_data)} gate(s) for batch insertion")
    print()


def main():
    """Run all tabular entity examples."""
    print("\n" + "=" * 60)
    print("EDA-Schema: Working with Tabular Entities")
    print("=" * 60 + "\n")

    create_complete_gate()
    create_port_collection()
    create_pin_collection()
    create_net_collection()
    demonstrate_entity_relationships()
    extract_tabular_data()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try 02_graph_entities.py to work with graph structures")
    print("  - Try 03_standard_cells.py to manage standard cell libraries")
    print()


if __name__ == "__main__":
    main()
