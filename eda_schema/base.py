import re
from functools import lru_cache
from dataclasses import dataclass, field, fields, Field, InitVar
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints
)

import numpy as np
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt


# ============================================================
# Type helpers
# ============================================================

def _is_optional_type(tp: Any) -> bool:
    return get_origin(tp) is Union and type(None) in get_args(tp)

def _unwrap_optional_type(tp: Any) -> Any:
    return next(t for t in get_args(tp) if t is not type(None))

@lru_cache(maxsize=None)
def _get_type_hints_cached(cls) -> Dict[str, Any]:
    """
    Cached version of typing.get_type_hints().
    Called once per entity class, never per instance.
    """
    return get_type_hints(cls, include_extras=True)

def _is_image_type(tp: Any) -> bool:
    """Return True if tp is Image2D or Optional[Image2D]."""
    if tp is Image2D:
        return True
    if _is_optional_type(tp):
        return _unwrap_optional_type(tp) is Image2D
    return False


@lru_cache(maxsize=None)
def _resolve_field_type_and_nullable_cached(
    model_cls: Type,
    field_name: str,
    field_metadata_items: tuple,
) -> Tuple[Optional[str], bool, bool]:
    """
    Resolve primitive json type + nullability + pk, cached per (class, field_name, pk-flag).

    Returns:
        (json_type, nullable, is_pk)
          - json_type: "string" | "integer" | "number" | "boolean" | None
          - nullable: True if Optional[...] / Union[..., None]
          - is_pk: True if field.metadata includes {"pk": True}
    """
    hints = _get_type_hints_cached(model_cls)
    tp = hints.get(field_name)  # prefer resolved type hints

    if tp is None:
        # Fallback shouldn't normally happen, but keep it safe:
        # if get_type_hints can't resolve for some reason, we don't know.
        nullable = False
        json_type = None
    else:
        nullable = False
        if _is_optional_type(tp):
            nullable = True
            tp = _unwrap_optional_type(tp)

        if tp is str:
            json_type = "string"
        elif tp is int:
            json_type = "integer"
        elif tp is float:
            json_type = "number"
        elif tp is bool:
            json_type = "boolean"
        else:
            json_type = None

    is_pk = bool(dict(field_metadata_items).get("pk", False))
    return json_type, nullable, is_pk


def resolve_field_type_and_nullable(
    model_cls: Type,
    f: Field,
) -> Tuple[Optional[str], bool, bool]:
    """
    Public wrapper for field resolution.

    Args:
        model_cls: The dataclass class that owns the field.
        f: A dataclasses.Field instance.

    Returns:
        (json_type, nullable, is_pk)
    """
    return _resolve_field_type_and_nullable_cached(
        model_cls,
        f.name,
        tuple(f.metadata.items()),
    )


def _is_image_field(model_cls: Type, f: Field) -> bool:
    """
    Return True if this dataclass field is Image2D or Optional[Image2D].

    Uses cached get_type_hints() so it works with:
        from __future__ import annotations
    """
    hints = _get_type_hints_cached(model_cls)
    tp = hints.get(f.name, f.type)
    return _is_image_type(tp)


# ============================================================
# Image2D (runtime-only, NumPy-native)
# ============================================================

class Image2D(np.ndarray):
    """
    2D NumPy array with lightweight runtime validation and plotting support.

    This class is intentionally:
    - Pydantic-free
    - Serialization-agnostic
    - Validation-on-demand
    """

    def __new__(cls, input_array):
        obj = np.asarray(input_array).view(cls)
        return obj

    def __array_finalize__(self, obj):
        pass

    def validate(self) -> None:
        """Validate Image2D invariants."""
        if not isinstance(self, np.ndarray):
            raise TypeError("Image2D must be a numpy ndarray")
        if self.ndim != 2:
            raise ValueError("Image2D must be 2D")
        if self.size == 0:
            raise ValueError("Image2D cannot be empty")

    def plot(self, filename: str, invert_mask: bool = False, cmap: str = "gray") -> None:
        """
        Save the image to disk.

        Supports:
        - Binary masks
        - Scalar heatmaps
        """
        unique_vals = np.unique(self)

        if unique_vals.size <= 2:
            mask = self.astype(np.uint8)
            if invert_mask:
                mask = 1 - mask
            rgb = np.zeros((*mask.shape, 3), dtype=np.uint8)
            rgb[mask == 1] = [255, 255, 255]
        else:
            norm = (self - self.min()) / (self.max() - self.min() + 1e-12)
            rgba = plt.cm.get_cmap(cmap)(norm)
            rgb = (rgba[:, :, :3] * 255).astype(np.uint8)

        h, w = rgb.shape[:2]
        fig = plt.figure(figsize=(w / 100, h / 100), frameon=False)
        ax = plt.Axes(fig, [0, 0, 1, 1])
        fig.add_axes(ax)
        ax.axis("off")
        ax.imshow(rgb)
        plt.savefig(filename, dpi=100, bbox_inches="tight", pad_inches=0)
        plt.close(fig)


# ============================================================
# BaseEntity (dataclass + shallow validation)
# ============================================================

@lru_cache(maxsize=None)
def _class_schema_metadata(
    cls: Type,
) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    """
    Compute and cache per-class schema metadata:

      - tabular keys: primitive fields (string/integer/number/boolean)
      - primary keys: fields marked with metadata {"pk": True}
      - image keys: Image2D or Optional[Image2D] fields

    Returns:
        (tabular_keys, primary_keys, image_keys) as tuples (immutable + cheap).
    """
    tabular: list[str] = []
    primary: list[str] = []
    image: list[str] = []

    for f in fields(cls):
        json_type, _, is_pk = resolve_field_type_and_nullable(cls, f)

        if json_type is not None:
            tabular.append(f.name)
        if is_pk:
            primary.append(f.name)
        if _is_image_field(cls, f):
            image.append(f.name)

    return (tuple(tabular), tuple(primary), tuple(image))


@dataclass(slots=True)
class BaseEntity:
    """
    Runtime base entity.

    Responsibilities:
    - Shallow type validation
    - Primary-key discovery
    - Tabular field extraction
    - Image field extraction
    """

    _tabular_keys: List[str] = field(init=False, repr=False)
    _primary_keys: List[str] = field(init=False, repr=False)
    _image_keys: List[str] = field(init=False, repr=False)

    def __post_init__(self):
        self._tabular_keys = []
        self._primary_keys = []
        self._image_keys = []

        self._tabular_keys, self._primary_keys, self._image_keys = _class_schema_metadata(type(self))
        self._post_init_hook()

    def _post_init_hook(self) -> None:
        """Optional hook for subclasses."""
        pass

    @classmethod
    def load(cls, data: Dict[str, Any]) -> "BaseEntity":
        """Instantiate and validate an entity from raw data."""
        obj = cls(**data)
        return obj

    def validate_types(self) -> None:
        """Perform shallow runtime type checking."""
        # Get resolved type hints (handles string annotations from __future__ import annotations)
        type_hints = _get_type_hints_cached(type(self))
        
        for f in fields(self):
            value = getattr(self, f.name)
            # Use resolved type hint if available, otherwise fall back to field.type
            expected = type_hints.get(f.name, f.type)

            if value is None:
                continue

            # Handle Optional types
            if _is_optional_type(expected):
                expected = _unwrap_optional_type(expected)

            # Handle generic types (Dict, List, etc.)
            origin = get_origin(expected)
            if origin is not None:
                # For generic types, validate the outer structure
                if origin is dict or origin is Dict:
                    if not isinstance(value, dict):
                        raise TypeError(
                            f"{f.name} expected dict, got {type(value)}"
                        )
                    # Skip deep validation of key/value types for complex generics
                    # (e.g., Dict[str, Image2D] - we can't easily validate Image2D values)
                elif origin is list or origin is List:
                    # Accept both list and tuple for List types (tuples are immutable sequences)
                    if not isinstance(value, (list, tuple)):
                        raise TypeError(
                            f"{f.name} expected list or tuple, got {type(value)}"
                        )
                    # Skip deep validation of item types for complex generics
                elif origin is tuple or origin is Tuple:
                    if not isinstance(value, tuple):
                        raise TypeError(
                            f"{f.name} expected tuple, got {type(value)}"
                        )
                # For other generic types, skip validation to avoid errors
                # (e.g., Union types, complex nested generics)
                continue

            # For non-generic types, use isinstance
            # Skip validation if expected is not a type (e.g., forward references, string annotations)
            if not isinstance(expected, type):
                # This can happen with forward references or other complex type annotations
                # Skip validation for these cases
                continue

            if expected is int and isinstance(value, bool):
                raise TypeError(f"{f.name} expected int, got bool")

            if not isinstance(value, expected):
                raise TypeError(
                    f"{f.name} expected {expected}, got {type(value)}"
                )

    def validate(self) -> None:
        """Override in subclasses for domain-specific validation."""
        self.validate_types()

    def get_tabular_data(self) -> Dict[str, Any]:
        """Return Arrow-compatible primitive fields."""
        return {k: getattr(self, k) for k in self._tabular_keys}

    def get_image_data(self) -> Dict[str, Optional[Image2D]]:
        """Return all Image2D fields."""
        return {k: getattr(self, k, None) for k in self._image_keys}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.get_tabular_data()})"

    __str__ = __repr__


# ============================================================
# GraphEntity (pure NetworkX, runtime-only)
# ============================================================

class GraphEntity(BaseEntity):
    """
    Runtime graph-backed entity.

    - Owns a directed NetworkX graph
    - Optionally enforces node typing
    """

    NODE_TYPES: Dict[str, Type[BaseEntity]] = {}
    graph_data: InitVar[Optional[Dict[str, Any]]] = None

    def _post_init_hook(self):
        self._graph = nx.DiGraph()

        if self.graph_data is not None:
            self.load_graph_data(self.graph_data)

    def _validate_node(self, node_id: str, attrs: Dict[str, Any]) -> None:
        if not self.NODE_TYPES:
            return

        node_type = attrs.get("type")
        entity = attrs.get("entity")

        if node_type not in self.NODE_TYPES:
            raise ValueError(
                f"Node '{node_id}' has invalid type '{node_type}'. "
                f"Allowed: {list(self.NODE_TYPES)}"
            )

        expected_cls = self.NODE_TYPES[node_type]
        if entity is not None and not isinstance(entity, expected_cls):
            raise TypeError(
                f"Node '{node_id}' expects {expected_cls.__name__}, "
                f"got {type(entity).__name__}"
            )

    @property
    def nodes(self):
        return self._graph.nodes

    @property
    def edges(self):
        return self._graph.edges

    def add_node(self, node_id: str, **attrs):
        self._validate_node(node_id, attrs)
        self._graph.add_node(node_id, **attrs)

    def add_edge(self, u: str, v: str, **attrs):
        self._graph.add_edge(u, v, **attrs)

    def predecessors(self, node: str):
        return self._graph.predecessors(node)

    def successors(self, node: str):
        return self._graph.successors(node)

    def subgraph(self, nodes):
        return self._graph.subgraph(nodes)

    def get_graph_data(self) -> Dict[str, Any]:
        nodes = list(self.nodes)
        return {
            "nodes": nodes,
            "node_types": [self.nodes[n].get("type") for n in nodes],
            "edges": [[u, v] for u, v in self.edges],
        }

    def load_graph_data(self, data: Dict[str, Any]) -> None:
        g = nx.DiGraph()
        for node, ntype in zip(data["nodes"], data["node_types"]):
            g.add_node(node, type=ntype, entity=None)
        for u, v in data["edges"]:
            g.add_edge(u, v)
        self._graph = g

    def bfs_traverse(
        self,
        node: str,
        fanin: bool = True,
        fanout: bool = True,
        depth_limit: int = -1,
        _visited: Optional[List[str]] = None,
        _level: int = 0,
    ) -> List[str]:
        if depth_limit == _level:
            return []

        visited = _visited or [node]
        neighbors = []

        if fanin:
            neighbors.extend(self._graph.predecessors(node))
        if fanout:
            neighbors.extend(self._graph.successors(node))

        new_nodes = [n for n in neighbors if n not in visited]
        visited.extend(new_nodes)

        for n in new_nodes:
            self.bfs_traverse(n, fanin, fanout, depth_limit, visited, _level + 1)

        return visited

    def dfs_traverse(
        self,
        node: str,
        fanin: bool = True,
        fanout: bool = True,
        depth_limit: int = -1,
        _visited: Optional[List[str]] = None,
        _level: int = 0,
    ) -> List[str]:
        if depth_limit == _level:
            return []

        visited = _visited or [node]
        neighbors = []

        if fanin:
            neighbors.extend(self._graph.predecessors(node))
        if fanout:
            neighbors.extend(self._graph.successors(node))

        for n in neighbors:
            if n not in visited:
                visited.append(n)
                self.dfs_traverse(n, fanin, fanout, depth_limit, visited, _level + 1)

        return visited

    def plot(
        self,
        figpath: Optional[str] = None,
        show: bool = True,
        filter_regex: Optional[str] = None,
    ):
        graph = (
            self._graph.subgraph(
                [n for n in self.nodes if not re.match(filter_regex, n)]
            )
            if filter_regex
            else self._graph
        )

        base_colors = [
            "#2CA02C", "#FF7F0E", "#9467BD", "#8C564B",
            "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF",
        ]

        type_list = list(self.NODE_TYPES.keys())
        color_map = {
            t: base_colors[i % len(base_colors)]
            for i, t in enumerate(type_list)
        }

        node_colors = [
            color_map.get(graph.nodes[n].get("type"), "#7F7F7F")
            for n in graph.nodes
        ]

        try:
            pos = graphviz_layout(graph, prog="dot")
        except Exception:
            pos = nx.spring_layout(graph)

        nx.draw(
            graph,
            pos,
            with_labels=True,
            arrows=True,
            node_color=node_colors,
            font_size=8,
        )

        if figpath:
            plt.savefig(figpath, bbox_inches="tight")
        if show:
            plt.show()
