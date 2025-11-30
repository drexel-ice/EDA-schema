import re
from typing import List, Optional, Tuple, Dict, Any, Type

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from pydantic import GetJsonSchemaHandler

import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import numpy as np
import pyarrow as pa



def resolve_schema_type_and_nullable(col_info: Dict[str, Any]) -> Tuple[Optional[str], bool]:
    """
    Resolve primitive type, nullability, and primary-key status from a
    Pydantic JSON Schema field definition.

    Args:
        col_info (Dict[str, Any]):
            JSON Schema fragment for one field.

    Returns:
        (json_type, nullable, is_pk):
            - json_type: "string", "integer", "number", "boolean", or None
            - nullable: True if null is allowed
            - is_pk: True if field metadata marks it as a primary key
    """
    nullable = False
    json_type = None

    # Extract primitive type + nullability
    if "type" in col_info:
        t = col_info["type"]
        if isinstance(t, list):
            for v in t:
                if v == "null":
                    nullable = True
                else:
                    json_type = v
        else:
            json_type = t

    elif "anyOf" in col_info:
        for variant in col_info["anyOf"]:
            vtype = variant.get("type")
            if vtype == "null":
                nullable = True
            elif vtype:
                json_type = vtype

    # Extract PK flag from metadata
    metadata = col_info.get("metadata", {})
    is_pk = bool(metadata.get("pk"))

    return json_type, nullable, is_pk


class BaseEntity(BaseModel):
    """Base class for EDA-schema entities with automatic Arrow type tracking."""

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    def __init__(self, *args, **kwargs):
        """
        Initialize the entity and collect property keys mapped to Arrow types.
        """
        super().__init__(*args, **kwargs)

        self._dict_keys = []
        self._primary_keys = []
        for name, schema in self.model_json_schema()["properties"].items():
            data_type, _, is_pk = resolve_schema_type_and_nullable(schema)
            if data_type:
                self._dict_keys.append(name)
            if is_pk:
                self._primary_keys.append(name)

    @classmethod
    def load(cls, data: Dict[str, Any]) -> "BaseEntity":
        """
        Instantiate the entity from raw field values.

        Args:
            data (dict): Field → value mapping.

        Returns:
            BaseEntity: A populated entity instance.

        Raises:
            ValidationError: If fields fail Pydantic validation.
        """
        try:
            return cls(**data)
        except ValidationError as e:
            raise e

    def asdict(self) -> Dict[str, Any]:
        """
        Return a filtered dictionary representation using Arrow-typed fields.

        Returns:
            dict: Key/value mapping.
        """
        model_data = self.model_dump()
        return {k: model_data[k] for k in self._dict_keys}

    def __repr__(self):
        return str(self.asdict())

    __str__ = __repr__


class GraphEntity(BaseEntity):
    """
    Base class containing an internal directed NetworkX graph.
    Child classes may define NODE_TYPES to enforce node → entity class mapping.
    """

    NODE_TYPES: Dict[str, Type[BaseEntity]] = {}

    def __init__(self, graph_dict: Optional[Dict[str, Any]] = None, **data):
        """
        Initialize the entity and optionally load a serialized graph structure.

        Args:
        graph_dict (dict | None):
            Optional serialized representation of a graph, produced by
            `graph_dict()`. If provided, the graph will be reconstructed
            immediately.
            **data: Base entity field values.
        """
        super().__init__(**data)
        self._graph = nx.DiGraph()
        if graph_dict is not None:
            self.load_graph_dict(graph_dict)

    def _validate_node(self, node_id: str, attrs: Dict[str, Any]):
        """
        Validate that a node satisfies declared NODE_TYPES.

        Args:
            node_id (str): Node identifier.
            attrs (dict): Attributes including 'type' and 'entity'.

        Raises:
            ValueError: If required attributes are missing or invalid.
            TypeError: If the entity does not match the required class.
        """
        if not self.NODE_TYPES:
            return

        node_type = attrs.get("type")
        entity = attrs.get("entity")

        if node_type is None:
            raise ValueError(f"Node '{node_id}' missing required field 'type'.")
        if entity is None:
            raise ValueError(f"Node '{node_id}' missing required field 'entity'.")

        if node_type not in self.NODE_TYPES:
            allowed = ", ".join(self.NODE_TYPES.keys())
            raise ValueError(
                f"Node '{node_id}' has invalid type '{node_type}'. Allowed: {allowed}"
            )

        required_cls = self.NODE_TYPES[node_type]
        if not isinstance(entity, required_cls):
            raise TypeError(
                f"Node '{node_id}' type '{node_type}' requires entity of type "
                f"{required_cls.__name__}, but got {type(entity).__name__}"
            )

    @property
    def nodes(self):
        """Return a NodeView of graph nodes."""
        return self._graph.nodes

    @property
    def edges(self):
        """Return an EdgeView of graph edges."""
        return self._graph.edges

    def add_node(self, node: str, **attrs):
        """
        Add a validated node to the graph.

        Args:
            node (str): Node name.
            **attrs: Node metadata including type/entity.
        """
        self._validate_node(node, attrs)
        self._graph.add_node(node, **attrs)

    def add_edge(self, u: str, v: str, **attrs):
        """
        Add a directed edge.

        Args:
            u (str): Source node.
            v (str): Destination node.
            **attrs: Additional edge metadata.
        """
        self._graph.add_edge(u, v, **attrs)

    def predecessors(self, node):
        """
        Return all predecessor nodes.

        Args:
            node (str): Target node.

        Returns:
            iterator: Predecessor node iterator.
        """
        return self._graph.predecessors(node)

    def successors(self, node):
        """
        Return all successor nodes.

        Args:
            node (str): Target node.

        Returns:
            iterator: Successor node iterator.
        """
        return self._graph.successors(node)

    def subgraph(self, nodes):
        """
        Extract a subgraph induced by the selected nodes.

        Args:
            nodes (Iterable[str]): Nodes to include in the subgraph.

        Returns:
            networkx.DiGraph: View of the subgraph.
        """
        return self._graph.subgraph(nodes)

    def graph_dict(self) -> Dict[str, Any]:
        """
        Produce a serializable summary of the graph.

        Returns:
            dict: {nodes, node_types, edges}
        """
        return {
            "nodes": list(self.nodes),
            "node_types": [self.nodes[n]["type"] for n in self.nodes],
            "edges": [list(e) for e in self.edges],
        }

    def load_graph_dict(self, data: Dict[str, Any]) -> None:
        """
        Reconstruct the internal NetworkX graph from a serialized graph dictionary.

        Args:
            data (dict):
                A dictionary with the exact structure returned by `graph_dict()`:
                    {
                        "nodes": [str, ...],
                        "node_types": [str, ...],
                        "edges": [[str, str], ...]
                    }
        """
        g = nx.DiGraph()
        for node_name, node_type in zip(data["nodes"], data["node_types"]):
            g.add_node(node_name, type=node_type, entity=None)

        for u, v in data["edges"]:
            g.add_edge(u, v)

        self._graph = g

    def get_node_inputs(self, node: str) -> List[str]:
        """
        List all predecessor nodes.

        Args:
            node (str): Node identifier.

        Returns:
            list[str]: Incoming neighbors.
        """
        return list(self._graph.predecessors(node))

    def get_node_outputs(self, node: str) -> List[str]:
        """
        List all successor nodes.

        Args:
            node (str): Node identifier.

        Returns:
            list[str]: Outgoing neighbors.
        """
        return list(self._graph.successors(node))

    def bfs_traverse(
        self,
        node: str,
        fanin: bool = True,
        fanout: bool = True,
        depth_limit: int = -1,
        _traversed: Optional[List[str]] = None,
        _level: int = 0,
    ) -> List[str]:
        """
        Perform a breadth-first traversal from a root node.

        Args:
            node (str): Start node.
            fanin (bool): Include predecessors.
            fanout (bool): Include successors.
            depth_limit (int): Maximum depth, -1 for unlimited.
            _traversed (list): Internal accumulator.
            _level (int): Recursion depth (internal).

        Returns:
            list[str]: Traversal order.
        """
        if depth_limit == _level:
            return []

        traversed = _traversed or [node]

        neighbors = []
        if fanin:
            neighbors.extend(self._graph.predecessors(node))
        if fanout:
            neighbors.extend(self._graph.successors(node))

        new_nodes = [n for n in neighbors if n not in traversed]
        traversed.extend(new_nodes)

        for nxt in new_nodes:
            self.bfs_traverse(nxt, fanin, fanout, depth_limit, traversed, _level + 1)

        return traversed

    def dfs_traverse(
        self,
        node: str,
        fanin: bool = True,
        fanout: bool = True,
        depth_limit: int = -1,
        _traversed: Optional[List[str]] = None,
        _level: int = 0,
    ) -> List[str]:
        """
        Perform a depth-first traversal from a root node.

        Args:
            node (str): Start node.
            fanin (bool): Include predecessors.
            fanout (bool): Include successors.
            depth_limit (int): Maximum recursion depth, -1 for unlimited.
            _traversed (list): Internal accumulator.
            _level (int): Current recursion depth.

        Returns:
            list[str]: DFS visitation order.
        """
        if depth_limit == _level:
            return []

        traversed = _traversed or [node]

        neighbors = []
        if fanin:
            neighbors.extend(self._graph.predecessors(node))
        if fanout:
            neighbors.extend(self._graph.successors(node))

        for nxt in neighbors:
            if nxt not in traversed:
                traversed.append(nxt)
                self.dfs_traverse(nxt, fanin, fanout, depth_limit, traversed, _level + 1)

        return traversed

    def plot(
        self,
        figpath: Optional[str] = None,
        show: bool = True,
        filter_regex: Optional[str] = None,
    ):
        """
        Visualize graph with colors based on this entity's NODE_TYPES mapping.
        Automatically handles PORT input/output colors.
        """
        if filter_regex:
            nodes = [n for n in self.nodes if not re.match(filter_regex, n)]
            graph = self._graph.subgraph(nodes)
        else:
            graph = self._graph

        # Color palette for each node type
        # NODE_TYPES is class-level mapping in each GraphEntity subclass.
        base_colors = [
            "#2CA02C",  # green
            "#FF7F0E",  # orange
            "#9467BD",  # purple
            "#8C564B",  # brown
            "#E377C2",  # pink
            "#7F7F7F",  # gray
            "#BCBD22",  # olive
            "#17BECF",  # cyan
        ]

        # Assign each NODE_TYPES key a color
        type_list = list(self.NODE_TYPES.keys())
        color_map_by_type = {
            t: base_colors[i % len(base_colors)] for i, t in enumerate(type_list)
        }

        # Special override for PORT directions
        input_color = "#D62728"  # red
        output_color = "#1F77B4" # blue

        node_colors = []
        for node in graph.nodes:
            data = graph.nodes[node]
            ntype = data.get("type")
            entity = data.get("entity")

            # PORTs with direction override
            if ntype == "PORT" and hasattr(entity, "direction"):
                if entity.direction == "INPUT":
                    node_colors.append(input_color)
                    continue
                if entity.direction == "OUTPUT":
                    node_colors.append(output_color)
                    continue

            # Default based on NODE_TYPES
            node_colors.append(color_map_by_type.get(ntype, "#7F7F7F"))

        legend_handles = []
        # Add PORT input/output first
        if "PORT" in type_list:
            legend_handles.append(
                mpatches.Patch(color=input_color, label="PORT INPUT")
            )
            legend_handles.append(
                mpatches.Patch(color=output_color, label="PORT OUTPUT")
            )

        # Add legend for all other NODE_TYPES
        for ntype, color in color_map_by_type.items():
            if ntype != "PORT":  # already handled separately
                legend_handles.append(mpatches.Patch(color=color, label=ntype))

        try:
            pos = graphviz_layout(graph, prog="dot")
        except Exception:
            pos = nx.spring_layout(graph)  # fallback

        nx.draw(
            graph,
            pos,
            with_labels=True,
            arrows=True,
            node_color=node_colors,
            font_size=8,
        )

        plt.legend(handles=legend_handles, loc="best")

        if figpath:
            plt.savefig(figpath, bbox_inches="tight")
        if show:
            plt.show()
        plt.close()


class Image2D:
    """2D NumPy array wrapper with Pydantic integration."""

    def __init__(self, array: np.ndarray):
        """
        Initialize an image wrapper around a 2D array.

        Args:
            array (np.ndarray): 2D numeric image matrix.

        Raises:
            TypeError: If not a NumPy array.
            ValueError: If not 2D.
        """
        if not isinstance(array, np.ndarray):
            raise TypeError("Image2D expects a numpy ndarray")
        if array.ndim != 2:
            raise ValueError("Image2D must be 2D")
        self.array = array

    @staticmethod
    def _validate_python(value: Any) -> "Image2D":
        """
        Validate and convert Python input types to Image2D.

        Args:
            value (Any): Array-like object.

        Returns:
            Image2D: Validated image instance.

        Raises:
            TypeError: If value is incompatible.
        """
        if isinstance(value, Image2D):
            return value
        if isinstance(value, np.ndarray):
            return Image2D(value)
        if isinstance(value, list):
            return Image2D(np.array(value))
        raise TypeError("Expected numpy.ndarray or 2D list")

    @staticmethod
    def _serialize(value: "Image2D") -> Any:
        """
        Serialize Image2D into a nested Python list.

        Args:
            value (Image2D): Image to serialize.

        Returns:
            list[list[float]]: Nested numeric lists.
        """
        return value.array.tolist()

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """
        Provide Pydantic core schema for both validation and serialization.

        Args:
            source_type: Type annotation from model.
            handler: Pydantic handler for sub-schemas.

        Returns:
            CoreSchema: Schema definition used internally by Pydantic.
        """
        base_schema = core_schema.list_schema(
            core_schema.list_schema(core_schema.float_schema())
        )

        return core_schema.no_info_wrap_validator_function(
            function=cls._validate_python,
            schema=core_schema.json_or_python_schema(
                json_schema=base_schema,
                python_schema=base_schema,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    cls._serialize, when_used="always"
                ),
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        """
        Provide the final JSON schema exposed externally.

        Args:
            schema (CoreSchema): Pydantic core schema.
            handler (GetJsonSchemaHandler): Delegates nested schema generation.

        Returns:
            dict: JSON schema for OpenAPI or external documentation.
        """
        json_schema = handler(schema)
        json_schema.update(
            {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {"type": "number"},
                },
                "description": "2D numeric matrix (image)",
            }
        )
        return json_schema
