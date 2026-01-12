#!/usr/bin/env python3
"""
Example: Working with Graph Entities

Description: Demonstrates creating and working with graph entities,
specifically NetlistEntity with nodes and edges.

Prerequisites:
- EDA-schema installed
- Understanding of graph structures

Key Concepts:
- Graph entity structure
- Node types (GATE, PORT, PIN, NET)
- Adding nodes and edges
- Graph traversal
- Graph data serialization

Usage:
    python examples/02_entities/02_graph_entities.py

See Also:
    - Tutorial: tutorials/04_graph_operations/
    - User Guide: docs/guides/user_guide.md#graph-operations
    - Examples: examples/04_graphs/
"""

from eda_schema import entity


def create_netlist():
    """Create a basic netlist entity."""
    print("=" * 60)
    print("Creating Netlist Entity")
    print("=" * 60)

    netlist = entity.NetlistEntity(
        flow_id='example_flow',
        stage='floorplan',
        no_of_inputs=2,
        no_of_outputs=1,
        no_of_cells=3,
        no_of_nets=4,
        no_of_pins=6,
        utilization=0.5,
        width=100.0,
        height=100.0
    )

    print(f"Netlist created:")
    print(f"  Flow ID: {netlist.flow_id}")
    print(f"  Stage: {netlist.stage}")
    print(f"  Cells: {netlist.no_of_cells}")
    print(f"  Nets: {netlist.no_of_nets}")
    print(f"  Pins: {netlist.no_of_pins}")
    print(f"  Utilization: {netlist.utilization:.2%}")
    print()

    return netlist


def add_nodes_to_netlist(netlist):
    """Add nodes (gates, ports, pins, nets) to the netlist."""
    print("=" * 60)
    print("Adding Nodes to Netlist")
    print("=" * 60)

    # Add input port
    clk_port = entity.PortEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='clk',
        direction='INPUT',
        x=0.0,
        y=0.0
    )
    netlist.add_node('clk', type='PORT', entity=clk_port)
    print("Added port: clk")

    # Add gates
    for i in range(3):
        gate = entity.GateEntity(
            flow_id='example_flow',
            stage='floorplan',
            name=f'U{i+1}',
            standard_cell='NAND2_X1',
            x_min=10.0 + i * 20.0,
            y_min=10.0,
            x_max=15.0 + i * 20.0,
            y_max=15.0,
            no_of_inputs=2,
            no_of_outputs=1
        )
        netlist.add_node(f'U{i+1}', type='GATE', entity=gate)
        print(f"Added gate: U{i+1}")

    # Add output port
    out_port = entity.PortEntity(
        flow_id='example_flow',
        stage='floorplan',
        name='out',
        direction='OUTPUT',
        x=100.0,
        y=0.0
    )
    netlist.add_node('out', type='PORT', entity=out_port)
    print("Added port: out")

    # Add nets
    nets = ['clk_net', 'net1', 'net2', 'out_net']
    for net_name in nets:
        net = entity.NetEntity(
            flow_id='example_flow',
            stage='floorplan',
            name=net_name,
            is_special_net=(net_name == 'clk_net'),
            no_of_fanouts=2,
            x_min=0.0,
            y_min=0.0,
            x_max=100.0,
            y_max=100.0,
            length=50.0
        )
        netlist.add_node(net_name, type='NET', entity=net)
        print(f"Added net: {net_name}")

    print(f"\nTotal nodes: {len(list(netlist.nodes))}")
    print()


def add_edges_to_netlist(netlist):
    """Add edges (connections) to the netlist."""
    print("=" * 60)
    print("Adding Edges to Netlist")
    print("=" * 60)

    # Connect clock port to clock net
    netlist.add_edge('clk', 'clk_net')
    print("clk -> clk_net")

    # Connect clock net to first gate
    netlist.add_edge('clk_net', 'U1')
    print("clk_net -> U1")

    # Connect gates in sequence
    netlist.add_edge('U1', 'net1')
    netlist.add_edge('net1', 'U2')
    print("U1 -> net1 -> U2")

    netlist.add_edge('U2', 'net2')
    netlist.add_edge('net2', 'U3')
    print("U2 -> net2 -> U3")

    # Connect last gate to output
    netlist.add_edge('U3', 'out_net')
    netlist.add_edge('out_net', 'out')
    print("U3 -> out_net -> out")

    print(f"\nTotal edges: {len(list(netlist.edges))}")
    print()


def traverse_netlist(netlist):
    """Demonstrate graph traversal."""
    print("=" * 60)
    print("Traversing Netlist Graph")
    print("=" * 60)

    # Count nodes by type
    node_counts = {}
    for node_id, node_data in netlist.nodes(data=True):
        node_type = node_data['type']
        node_counts[node_type] = node_counts.get(node_type, 0) + 1

    print("Node counts by type:")
    for node_type, count in node_counts.items():
        print(f"  {node_type}: {count}")
    print()

    # Find all gates
    gates = [n for n, d in netlist.nodes(data=True) if d['type'] == 'GATE']
    print(f"Gates: {gates}")

    # Find all ports
    ports = [n for n, d in netlist.nodes(data=True) if d['type'] == 'PORT']
    print(f"Ports: {ports}")
    print()

    # Show connectivity
    print("Connectivity:")
    for node_id in list(netlist.nodes)[:5]:  # Show first 5 nodes
        successors = list(netlist._graph.successors(node_id))
        predecessors = list(netlist._graph.predecessors(node_id))
        print(f"  {node_id}:")
        if predecessors:
            print(f"    <- {predecessors}")
        if successors:
            print(f"    -> {successors}")
    print()


def demonstrate_graph_operations(netlist):
    """Demonstrate graph operations."""
    print("=" * 60)
    print("Graph Operations")
    print("=" * 60)

    # Get node degree
    print("Node degrees:")
    for node_id in ['U1', 'U2', 'clk_net']:
        if node_id in netlist.nodes:
            in_degree = netlist._graph.in_degree(node_id)
            out_degree = netlist._graph.out_degree(node_id)
            print(f"  {node_id}: in={in_degree}, out={out_degree}")
    print()

    # Create subgraph
    subgraph_nodes = ['clk', 'clk_net', 'U1']
    subgraph = netlist.subgraph(subgraph_nodes)
    print(f"Subgraph with {len(list(subgraph.nodes))} nodes:")
    for node in subgraph.nodes:
        print(f"  - {node}")
    print()

    # Check if path exists
    if 'clk' in netlist.nodes and 'U1' in netlist.nodes:
        try:
            import networkx as nx
            has_path = nx.has_path(netlist._graph, 'clk', 'U1')
            print(f"Path exists from 'clk' to 'U1': {has_path}")
        except ImportError:
            print("NetworkX not available for path checking")
    print()


def serialize_graph_data(netlist):
    """Demonstrate graph data serialization."""
    print("=" * 60)
    print("Graph Data Serialization")
    print("=" * 60)

    # Get graph data for storage
    graph_data = netlist.get_graph_data()

    print("Graph data structure:")
    print(f"  Nodes: {len(graph_data['nodes'])}")
    print(f"  Node types: {len(graph_data['node_types'])}")
    print(f"  Edges: {len(graph_data['edges'])}")
    print()

    print("Sample graph data:")
    print(f"  First 3 nodes: {graph_data['nodes'][:3]}")
    print(f"  First 3 edges: {graph_data['edges'][:3]}")
    print()

    # Demonstrate loading graph data
    new_netlist = entity.NetlistEntity(
        flow_id='example_flow',
        stage='floorplan',
        no_of_inputs=2,
        no_of_outputs=1,
        no_of_cells=3,
        no_of_nets=4,
        no_of_pins=6,
        utilization=0.5,
        width=100.0,
        height=100.0
    )
    new_netlist.load_graph_data(graph_data)
    print(f"Loaded graph data into new netlist: {len(list(new_netlist.nodes))} nodes")
    print()


def main():
    """Run all graph entity examples."""
    print("\n" + "=" * 60)
    print("EDA-Schema: Working with Graph Entities")
    print("=" * 60 + "\n")

    # Create netlist
    netlist = create_netlist()

    # Add nodes and edges
    add_nodes_to_netlist(netlist)
    add_edges_to_netlist(netlist)

    # Traverse and analyze
    traverse_netlist(netlist)
    demonstrate_graph_operations(netlist)
    serialize_graph_data(netlist)

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try 03_standard_cells.py to work with standard cell libraries")
    print("  - Try examples/04_graphs/ for advanced graph operations")
    print()


if __name__ == "__main__":
    main()
