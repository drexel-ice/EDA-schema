#!/usr/bin/env python3
"""
Example: Netlist Traversal

Description: Demonstrates traversing netlist graphs, including node iteration,
edge traversal, and path finding.

Prerequisites:
- EDA-schema installed
- A dataset with netlist data

Key Concepts:
- Graph traversal
- Node and edge iteration
- Path finding
- Graph structure analysis

Usage:
    python examples/04_graphs/01_netlist_traversal.py [dataset_path]

See Also:
    - Interactive Notebook: notebooks/tutorials/04_graph_operations.ipynb
    - Tutorial: tutorials/04_graph_operations/
    - User Guide: docs/guides/user_guide.md#graph-operations
    - How-To: docs/howto/analyze_netlists.md
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def traverse_nodes(netlist):
    """Traverse all nodes in a netlist."""
    print("=" * 60)
    print("Traversing Nodes")
    print("=" * 60)

    node_counts = {}
    for node_id, node_data in netlist.nodes(data=True):
        node_type = node_data['type']
        node_counts[node_type] = node_counts.get(node_type, 0) + 1

    print("Node counts by type:")
    for node_type, count in sorted(node_counts.items()):
        print(f"  {node_type}: {count}")

    print(f"\nTotal nodes: {len(list(netlist.nodes))}")
    print()


def traverse_edges(netlist):
    """Traverse all edges in a netlist."""
    print("=" * 60)
    print("Traversing Edges")
    print("=" * 60)

    edge_count = 0
    for source, target in netlist.edges:
        edge_count += 1
        if edge_count <= 10:  # Show first 10
            source_type = netlist.nodes[source]['type']
            target_type = netlist.nodes[target]['type']
            print(f"  {source} ({source_type}) -> {target} ({target_type})")

    if edge_count > 10:
        print(f"  ... and {edge_count - 10} more edges")

    print(f"\nTotal edges: {edge_count}")
    print()


def find_paths(netlist):
    """Find paths in the netlist."""
    print("=" * 60)
    print("Finding Paths")
    print("=" * 60)

    try:
        import networkx as nx

        # Find input ports
        input_ports = [n for n, d in netlist.nodes(data=True) 
                      if d['type'] == 'PORT' and 
                      d.get('entity') and 
                      d['entity'].direction == 'INPUT']

        # Find output ports
        output_ports = [n for n, d in netlist.nodes(data=True)
                       if d['type'] == 'PORT' and
                       d.get('entity') and
                       d['entity'].direction == 'OUTPUT']

        print(f"Input ports: {len(input_ports)}")
        print(f"Output ports: {len(output_ports)}")

        # Find paths from inputs to outputs
        if input_ports and output_ports:
            paths_found = 0
            for input_port in input_ports[:3]:  # Check first 3 inputs
                for output_port in output_ports[:3]:  # Check first 3 outputs
                    if nx.has_path(netlist._graph, input_port, output_port):
                        try:
                            path = nx.shortest_path(netlist._graph, input_port, output_port)
                            if len(path) > 2:  # More than just direct connection
                                print(f"\nPath from {input_port} to {output_port}:")
                                print(f"  Length: {len(path)} nodes")
                                print(f"  Path: {' -> '.join(path[:5])}...")
                                paths_found += 1
                                if paths_found >= 3:
                                    break
                        except:
                            pass
                if paths_found >= 3:
                    break

    except ImportError:
        print("NetworkX not available for path finding")
    except Exception as e:
        print(f"Error finding paths: {e}")

    print()


def analyze_connectivity(netlist):
    """Analyze graph connectivity."""
    print("=" * 60)
    print("Connectivity Analysis")
    print("=" * 60)

    # Node degrees
    high_degree_nodes = []
    for node_id in netlist.nodes:
        in_degree = netlist._graph.in_degree(node_id)
        out_degree = netlist._graph.out_degree(node_id)
        total_degree = in_degree + out_degree

        if total_degree > 5:
            node_type = netlist.nodes[node_id]['type']
            high_degree_nodes.append((node_id, node_type, total_degree))

    if high_degree_nodes:
        print("High-degree nodes (>5 connections):")
        for node_id, node_type, degree in sorted(high_degree_nodes, 
                                                  key=lambda x: x[2], 
                                                  reverse=True)[:10]:
            print(f"  {node_id} ({node_type}): {degree} connections")
    else:
        print("No high-degree nodes found")

    # Find isolated nodes (if any)
    isolated = [n for n in netlist.nodes 
                if netlist._graph.degree(n) == 0]
    if isolated:
        print(f"\nIsolated nodes: {len(isolated)}")
    else:
        print("\nNo isolated nodes")

    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 01_netlist_traversal.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("\n" + "=" * 60)
    print("EDA-Schema: Netlist Traversal")
    print("=" * 60 + "\n")

    # Load dataset
    db = ParquetDB(str(dataset_path))
    dataset = Dataset(db)
    dataset.load_standard_cells()

    # Try to load a netlist
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
        netlist = dataset.load_netlist(flow_id, stage)

        # Traverse netlist
        traverse_nodes(netlist)
        traverse_edges(netlist)
        find_paths(netlist)
        analyze_connectivity(netlist)

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
