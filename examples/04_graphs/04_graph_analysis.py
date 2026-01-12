#!/usr/bin/env python3
"""
Example: Advanced Graph Analysis

Description:
Demonstrates advanced graph analysis techniques using NetworkX
and scalable custom algorithms suitable for large netlists.

Prerequisites:
- EDA-schema installed
- NetworkX
- A dataset with netlist data

Key Concepts:
- NetworkX integration
- Graph metrics
- Connectivity analysis
- Scalable cycle detection
- Structural netlist analysis

Usage:
    python examples/04_graphs/04_graph_analysis.py [dataset_path]
"""

import sys
from pathlib import Path

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB


def networkx_analysis(netlist):
    """Perform basic NetworkX-based analysis."""
    print("=" * 60)
    print("NetworkX Analysis")
    print("=" * 60)

    try:
        import networkx as nx

        graph = netlist._graph

        print("Graph Metrics:")
        print(f"  Nodes: {graph.number_of_nodes()}")
        print(f"  Edges: {graph.number_of_edges()}")
        print(f"  Density: {nx.density(graph):.6f}")
        print(f"  Is DAG: {nx.is_directed_acyclic_graph(graph)}")

        if nx.is_weakly_connected(graph):
            print("  Graph is weakly connected")
        else:
            components = list(nx.weakly_connected_components(graph))
            print(f"  Weakly connected components: {len(components)}")

        print("\nCentrality Analysis:")

        degree_centrality = nx.degree_centrality(graph)
        top_nodes = sorted(
            degree_centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        print("  Top 5 nodes by degree centrality:")
        for node, centrality in top_nodes:
            node_type = netlist.nodes[node]["type"]
            print(f"    {node} ({node_type}): {centrality:.4f}")

    except ImportError:
        print("NetworkX not available")
    except Exception as e:
        print(f"Error in NetworkX analysis: {e}")

    print()


def analyze_node_types(netlist):
    """Analyze distribution and degree statistics of node types."""
    print("=" * 60)
    print("Node Type Analysis")
    print("=" * 60)

    type_stats = {}

    graph = netlist._graph

    for node_id, node_data in netlist.nodes(data=True):
        node_type = node_data["type"]

        if node_type not in type_stats:
            type_stats[node_type] = {
                "count": 0,
                "in_degree_sum": 0,
                "out_degree_sum": 0,
            }

        stats = type_stats[node_type]
        stats["count"] += 1
        stats["in_degree_sum"] += graph.in_degree(node_id)
        stats["out_degree_sum"] += graph.out_degree(node_id)

    for node_type, stats in sorted(type_stats.items()):
        avg_in = stats["in_degree_sum"] / stats["count"]
        avg_out = stats["out_degree_sum"] / stats["count"]

        print(f"  {node_type}:")
        print(f"    Count: {stats['count']}")
        print(f"    Avg in-degree: {avg_in:.2f}")
        print(f"    Avg out-degree: {avg_out:.2f}")

    print()


def find_cycles(netlist):
    """
    Detect cycles using strongly connected components.

    This method is linear-time and safe for large netlists.
    """
    print("=" * 60)
    print("Cycle Detection")
    print("=" * 60)

    try:
        import networkx as nx

        graph = netlist._graph

        sccs = nx.strongly_connected_components(graph)
        cyclic_components = [c for c in sccs if len(c) > 1]

        if not cyclic_components:
            print("Graph is acyclic (no cycles detected)")
            print()
            return

        print(f"Detected {len(cyclic_components)} cyclic component(s)")

        print("\nLargest cyclic components:")
        largest = sorted(cyclic_components, key=len, reverse=True)[:5]

        for i, comp in enumerate(largest, 1):
            preview = list(comp)[:5]
            print(f"  Component {i}:")
            print(f"    Size: {len(comp)}")
            print(f"    Nodes: {', '.join(preview)}...")

    except ImportError:
        print("NetworkX not available for cycle detection")
    except Exception as e:
        print(f"Error during cycle detection: {e}")

    print()


def analyze_connectivity_patterns(netlist):
    """Analyze high-fanin and high-fanout connectivity patterns."""
    print("=" * 60)
    print("Connectivity Patterns")
    print("=" * 60)

    graph = netlist._graph

    high_fanout = []
    high_fanin = []

    for node_id in netlist.nodes:
        out_degree = graph.out_degree(node_id)
        in_degree = graph.in_degree(node_id)
        node_type = netlist.nodes[node_id]["type"]

        if out_degree > 10:
            high_fanout.append((node_id, node_type, out_degree))

        if in_degree > 10:
            high_fanin.append((node_id, node_type, in_degree))

    if high_fanout:
        print(f"High-fanout nodes (>10 outputs): {len(high_fanout)}")
        for node_id, node_type, degree in sorted(
            high_fanout, key=lambda x: x[2], reverse=True
        )[:10]:
            print(f"  {node_id} ({node_type}): {degree} outputs")
    else:
        print("No high-fanout nodes found")

    if high_fanin:
        print(f"\nHigh-fanin nodes (>10 inputs): {len(high_fanin)}")
        for node_id, node_type, degree in sorted(
            high_fanin, key=lambda x: x[2], reverse=True
        )[:10]:
            print(f"  {node_id} ({node_type}): {degree} inputs")
    else:
        print("\nNo high-fanin nodes found")

    print()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        dataset_path = Path(sys.argv[1])
    else:
        dataset_path = Path(__file__).parent.parent.parent / "dataset" / "test"
        if not dataset_path.exists():
            print("Usage: python 04_graph_analysis.py <dataset_path>")
            sys.exit(1)
        print(f"Using dataset: {dataset_path}\n")

    print("=" * 60)
    print("EDA-Schema: Advanced Graph Analysis")
    print("=" * 60)
    print()

    db = ParquetDB(str(dataset_path))
    dataset = Dataset(db)
    dataset.load_standard_cells()

    try:
        flows_df = dataset.db.get_table_data("design_flows")
        if flows_df.empty:
            print("No design flows found")
            return

        flow_id = flows_df.iloc[0]["flow_id"]
        stages_df = dataset.db.get_table_data(
            "design_stages", flow_id=flow_id
        )

        if stages_df.empty:
            print("No design stages found")
            return

        stage = stages_df.iloc[0]["stage"]
        netlist = dataset.load_netlist(flow_id, stage)

        networkx_analysis(netlist)
        analyze_node_types(netlist)
        find_cycles(netlist)
        analyze_connectivity_patterns(netlist)

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
