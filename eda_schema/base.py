import re
from typing import List, Optional, Dict, Any

import jsonschema
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from eda_schema.errors import ValidationError


LEGEND_HANDLES = [
    mpatches.Patch(color="red", label="INPUT"),
    mpatches.Patch(color="green", label="GATE"),
    mpatches.Patch(color="orange", label="PIN"),
    mpatches.Patch(color="yellow", label="INTERCONNECT"),
    mpatches.Patch(color="blue", label="OUTPUT"),
]

class BaseEntity:
    """Base class for JSON schema validation and attribute setting."""

    def __init__(self, json_data: Dict[str, Any] = None, validate: bool = True) -> None:
        """
        Initialize the BaseEntity instance.

        Args:
            json_data (dict, optional): JSON data to validate and set as attributes.
            validate (bool, optional): Whether to validate the JSON data before setting attributes. Defaults to True.
        """
        if json_data:
            self.load(json_data, validate=validate)

    def load(self, json_data: Dict[str, Any], validate: bool = True) -> None:
        """
        Load and validate JSON data, setting attributes.

        Args:
            json_data (dict): JSON data to load and validate.
            validate (bool, optional): Whether to validate the JSON data before setting attributes. Defaults to True.
        """
        if validate:
            self.validate(json_data)
        for attr, value in json_data.items():
            setattr(self, attr, value)

    def validate(self, json_data: Dict[str, Any]) -> None:
        """
        Validate JSON data against the schema.

        Args:
            json_data (dict): JSON data to validate.

        Raises:
            ValidationError: If JSON data does not conform to the schema.
        """
        try:
            jsonschema.validate([json_data], self.schema)
        except jsonschema.exceptions.ValidationError as msg:
            raise ValidationError(msg)

    def asdict(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary representation.

        Returns:
            dict: Dictionary representation of the object attributes.
        """
        return {attr: getattr(self, attr) for attr in self.schema["items"]["properties"]}

    def __repr__(self):
        return str(self.asdict())

    def __str__(self):
        return str(self.asdict())


class GraphEntity(nx.DiGraph, BaseEntity):
    """Base class for JSON schema validation and attribute setting."""

    def __init__(self, json_data: Dict[str, Any] = None, validate: bool = True) -> None:
        """
        Initialize the BaseEntity instance.

        Args:
            json_data (dict, optional): JSON data to validate and set as attributes.
        """
        super().__init__()
        BaseEntity().__init__(validate=validate)
        if json_data:
            self.load(json_data)

    def __repr__(self):
        return str(self.asdict())

    def __str__(self):
        return str(self.asdict())

    def graph_dict(self):
        return {
            "nodes": [node for node in self.nodes],
            "node_types": [self.nodes[node]["type"] for node in self.nodes],
            "edges": [list(edge) for edge in self.edges],
        }

    def get_node_inputs(self, node: str) -> List[str]:
        """Get all netlist inputs.

        Args:
            node (str): Name of netlist node.

        Returns:
            list: All inputs of netlist.
        """
        return list(self.predecessors(node))

    def get_node_outputs(self, node: str) -> List[str]:
        """
        Get all netlist outputs.

        Args:
            node (str): Name of netlist node.

        Returns:
            list: All outputs of netlist.
        """
        return list(self.successors(node))

    def bfs_traverse(
        self,
        node: str,
        fanin: bool = True,
        fanout: bool = True,
        depth_limit: int = -1,
        _traversed_node: Optional[List[str]] = None,
        _current_level: int = 0,
    ) -> List[str]:
        """Breadth first traversal of netlist graph

        Args:
            node (str):  Name of netlist node to set as root node.
            fanin (bool): Traverse through inputs if true.
            fanout (bool): Traverse through outputs if true.
            depth_limit (int, optional): Limit level of travesal. -1 signifies no limit.

        Returns:
            list: All traversed nodes.

        Complexity:
            - Time Complexity:
                - O(V + E) in the worst case, where V is the number of nodes and E is the number of edges.
                - If `depth_limit = d`, then the traversal may explore up to O(b^d) nodes, where `b` is the branching factor (average no. of neighbors).
            - Space Complexity:
                - O(V) in the worst case (when all nodes are stored in the queue).
                - If `depth_limit = d`, then space complexity is at most O(b^d).
        """
        if depth_limit == _current_level:
            return []
        traversed_node = _traversed_node or [node]

        node_list = []
        if fanin:
            node_list += self.get_node_inputs(node)
        if fanout:
            node_list += self.get_node_outputs(node)

        neighbor_nodes = []
        for neighbor_node in node_list:
            if neighbor_node not in traversed_node:
                neighbor_nodes.append(neighbor_node)

        traversed_node += neighbor_nodes

        for neighbor_node in neighbor_nodes:
            self.bfs_traverse(
                neighbor_node,
                fanin=fanin,
                fanout=fanout,
                depth_limit=depth_limit,
                _traversed_node=traversed_node,
                _current_level=_current_level + 1,
            )

        return traversed_node

    def dfs_traverse(
        self,
        node: str,
        fanin: bool = True,
        fanout: bool = True,
        depth_limit: int = -1,
        _traversed_node: Optional[List[str]] = None,
        _current_level: int = 0,
    ) -> List[str]:
        """Depth-first traversal of a netlist graph.

        Args:
            node (str): Name of the netlist node to set as the root node.
            fanin (bool): Traverse through inputs if true.
            fanout (bool): Traverse through outputs if true.
            depth_limit (int, optional): Limit level of traversal. -1 signifies no limit.

        Returns:
            list: All traversed nodes.

        Complexity:
            - Time Complexity:
                - O(V + E) in the worst case, where V is the number of nodes and E is the number of edges.
                - If `depth_limit = d`, then the traversal may explore up to O(b^d) nodes, where `b` is the branching factor (average no. of neighbors).
            - Space Complexity:
                - O(V) in the worst case due to recursion depth (stack space).
                - If `depth_limit = d`, then space complexity is at most O(d) due to recursive calls.
        """
        if depth_limit == _current_level:
            return []
        traversed_node = _traversed_node or [node]

        node_list = []
        if fanin:
            node_list += self.get_node_inputs(node)
        if fanout:
            node_list += self.get_node_outputs(node)

        for neighbor_node in node_list:
            if neighbor_node in traversed_node:
                continue
            traversed_node.append(neighbor_node)
            self.dfs_traverse(
                neighbor_node,
                fanin=fanin,
                fanout=fanout,
                depth_limit=depth_limit,
                _traversed_node=traversed_node,
                _current_level=_current_level + 1,
            )

        return traversed_node

    def plot(self, figpath=None, show=True, filter_regex=None):
        color_map = []
        if filter_regex:
            node_list = [node for node in self.nodes if not re.match(filter_regex, node)]
            graph = self.subgraph(node_list)
        else:
            graph = self

        for node in graph.nodes:
            entity = graph.nodes[node]["entity"]
            entity_type = graph.nodes[node]["type"]
            if entity_type == "PORT" and entity.direction == "INPUT":
                color_map.append("red")
            if entity_type == "PORT" and entity.direction == "OUTPUT":
                color_map.append("blue")
            if entity_type == "GATE":
                color_map.append("green")
            if entity_type == "INTERCONNECT":
                color_map.append("yellow")
            if entity_type == "PIN":
                color_map.append("orange")

        pos = graphviz_layout(graph, prog="dot")
        plt.legend(handles=LEGEND_HANDLES, loc="best")
        nx.draw(graph, pos, with_labels=True, arrows=True, node_color=color_map)

        if figpath:
            plt.savefig(figpath)
        if show:
            plt.show()
