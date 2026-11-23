# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/server.py
# Authors :
#     Alec Aversa
#
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike
# 4.0 International License (CC BY-NC-SA 4.0). You may obtain a copy of the
# license at: https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. Commercial use is
# expressly prohibited; derivative works must be shared under the same
# license terms (ShareAlike).

"""MCP server for one EDA-Schema dataset.

Run it with::

    eda-schema-mcp --dataset /path/to/<pdk-dataset>
    # or
    EDA_SCHEMA_DATASET=/path/to/<pdk-dataset> python -m eda_schema.mcp

Tool logic lives in :mod:`eda_schema.mcp.tools` as plain functions whose first
argument is the :class:`~eda_schema.mcp.context.DatasetContext`. This module
binds them to one context and registers them with an
:class:`mcp.server.mcpserver.MCPServer`.
"""

from __future__ import annotations

import argparse
import base64
import functools
import inspect
import json
import logging
import os
import sys
import typing
from collections.abc import Callable, Sequence
from dataclasses import fields as dc_fields
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from mcp.types import CallToolResult, ImageContent, TextContent, ToolAnnotations

from eda_schema.entity import SchemaMetadata
from eda_schema.mcp.context import STAGES, DatasetContext
from eda_schema.mcp.envelope import clean, dumps
from eda_schema.mcp.errors import DatasetRootError, McpInputError
from eda_schema.mcp.tools import catalog, images, netlist, qor, timing
from eda_schema.mcp.tools.images import ImageResult

logger = logging.getLogger(__name__)

ENV_DATASET = "EDA_SCHEMA_DATASET"

#: Phase 1 tools, in the order they are listed to clients.
TOOLS: list[Callable[..., Any]] = [
    catalog.get_dataset_info,
    catalog.list_designs,
    catalog.list_flows,
    catalog.get_flow,
    qor.get_qor,
    qor.get_stage_evolution,
    qor.compare_flows,
    qor.aggregate_metrics,
    timing.get_timing_summary,
    timing.list_timing_paths,
    timing.get_timing_path,
    netlist.get_netlist_summary,
    images.list_images,
    images.render_image,
]

READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


def instructions_for(ctx: DatasetContext) -> str:
    """Server instructions sent to the client at initialization."""
    return (
        f"EDA-Schema dataset server for PDK '{ctx.pdk}' ({len(ctx.flows)} flows, "
        f"{len(ctx.designs)} designs). Read-only.\n"
        f"- This server serves the '{ctx.pdk}' dataset only. Do not compare its numbers "
        "with other eda-schema servers; cross-PDK comparison is not supported.\n"
        "- Start with get_dataset_info, then list_designs / list_flows to find flow ids.\n"
        "- Prefer summaries (get_qor, get_timing_summary, aggregate_metrics, "
        "get_netlist_summary) over row listings.\n"
        "- List tools are paginated: when 'truncated' is true, pass 'next_cursor' back "
        "as 'cursor', or follow the 'hint'.\n"
        f"- Stages in flow order: {', '.join(STAGES)}."
    )


def to_call_result(result: Any) -> CallToolResult:
    """Convert a tool function's return value into an MCP ``CallToolResult``."""
    if isinstance(result, ImageResult):
        return CallToolResult(
            content=[
                ImageContent(
                    type="image",
                    data=base64.b64encode(result.png).decode("ascii"),
                    mime_type="image/png",
                ),
                TextContent(type="text", text=dumps(result.info)),
            ],
            structured_content=result.info,
        )
    return CallToolResult(
        content=[TextContent(type="text", text=dumps(result))],
        structured_content=result,
    )


def bind(ctx: DatasetContext, fn: Callable[..., Any]) -> Callable[..., CallToolResult]:
    """Bind ``fn(ctx, **kwargs)`` to ``ctx`` as an MCP tool function.

    The returned wrapper has ``fn``'s signature without ``ctx`` (so the SDK
    builds the input schema from the original annotations), converts results
    with :func:`to_call_result` and turns :class:`McpInputError` into a
    ``ToolError`` the model can read.
    """
    sig = inspect.signature(fn)
    hints = typing.get_type_hints(fn, include_extras=True)
    hints.pop("ctx", None)
    hints["return"] = CallToolResult
    # Resolve string annotations (modules use `from __future__ import annotations`)
    # so the SDK never has to evaluate them in this module's namespace.
    params = [
        p.replace(annotation=hints.get(p.name, p.annotation))
        for p in list(sig.parameters.values())[1:]
    ]

    @functools.wraps(fn)
    def wrapper(**kwargs: Any) -> CallToolResult:
        try:
            return to_call_result(fn(ctx, **kwargs))
        except McpInputError as exc:
            raise ToolError(str(exc)) from exc

    del wrapper.__wrapped__  # make the SDK use __signature__, not fn's
    wrapper.__signature__ = sig.replace(parameters=params, return_annotation=CallToolResult)  # type: ignore[attr-defined]
    wrapper.__annotations__ = hints
    return wrapper


def _resource(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Map anticipated lookup errors in resources to ``ResourceError``."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except McpInputError as exc:
            raise ResourceError(str(exc)) from exc

    return wrapper


def schema_summary(ctx: DatasetContext, entity_name: str | None = None) -> dict[str, Any]:
    """Entity fields with presence in this dataset (``eda://schema`` resources)."""
    names = [n for n, _ in SchemaMetadata.items()]
    if entity_name is not None and entity_name not in names:
        from eda_schema.mcp.errors import not_found

        raise not_found("entity", entity_name, names)

    def describe(name: str) -> dict[str, Any]:
        model = SchemaMetadata.get_model(name)
        present = set(ctx.entity_columns.get(name, []))
        cols, imgs, missing = [], [], []
        for f in dc_fields(model):
            if f.name.startswith("_"):
                continue
            type_name = getattr(f.type, "__name__", None) or str(f.type)
            if "Image2D" in str(f.type):
                imgs.append(f.name)
            elif "Entity" in str(f.type):
                continue  # nested sub-entities, stored in their own tables
            elif f.name in present:
                cols.append({"name": f.name, "type": type_name})
            else:
                missing.append(f.name)
        info: dict[str, Any] = {
            "primary_key": SchemaMetadata.get_pk_columns(name),
            "graph": SchemaMetadata.is_graph_entity(name),
            "rows": ctx.entity_rows.get(name),
            "columns": cols,
        }
        if imgs:
            info["images"] = imgs
        if missing:
            info["defined_but_absent"] = missing
        node_types = getattr(model, "NODE_TYPES", None)
        if node_types:
            info["graph_node_types"] = sorted(node_types)
        if model.__doc__:
            info["description"] = model.__doc__.strip().splitlines()[0]
        return info

    if entity_name is not None:
        return {"entity": entity_name, **describe(entity_name)}
    return {"entities": {n: describe(n) for n in names}}


def register_resources(server: MCPServer, ctx: DatasetContext) -> None:
    """Register the section 6.1 resources."""
    as_json = functools.partial(lambda obj: json.dumps(clean(obj, ctx.precision), indent=1))

    @server.resource(
        "eda://dataset",
        name="dataset",
        mime_type="application/json",
        description="PDK, identity, units, counts and limits of this dataset.",
    )
    def dataset_resource() -> str:
        return as_json(catalog.dataset_info(ctx))

    @server.resource(
        "eda://dataset/summary",
        name="dataset_summary",
        mime_type="application/json",
        description="Designs with flow counts and run-status breakdown.",
    )
    def summary_resource() -> str:
        return as_json({"pdk": ctx.pdk, "designs": catalog.designs_table(ctx)})

    @server.resource(
        "eda://schema",
        name="schema",
        mime_type="application/json",
        description="All entities: primary keys, columns present, images, absent fields.",
    )
    def schema_resource() -> str:
        return as_json(schema_summary(ctx))

    @server.resource(
        "eda://schema/{entity}",
        name="schema_entity",
        mime_type="application/json",
        description="One entity's fields and their presence in this dataset.",
    )
    @_resource
    def schema_entity_resource(entity: str) -> str:
        return as_json(schema_summary(ctx, entity))

    @server.resource(
        "eda://stages",
        name="stages",
        mime_type="application/json",
        description="Design stages in flow order with the image kinds stored per stage.",
    )
    def stages_resource() -> str:
        per_stage: dict[str, set] = {s: set() for s in STAGES}
        for (_, stage), refs in ctx.images.items():
            for ref in refs:
                per_stage.setdefault(stage, set()).add(f"{ref.entity}/{ref.name}")
        return as_json(
            {
                "stages": [
                    {"stage": s, "order": i, "image_kinds": sorted(per_stage.get(s, ()))}
                    for i, s in enumerate(STAGES)
                ]
            }
        )

    @server.resource(
        "eda://flows/{flow_id}",
        name="flow",
        mime_type="application/json",
        description="One flow: design, run status, constraints, per-stage status.",
    )
    @_resource
    def flow_resource(flow_id: str) -> str:
        return as_json(catalog.flow_detail(ctx, flow_id))

    @server.resource(
        "eda://flows/{flow_id}/{stage}/qor",
        name="flow_stage_qor",
        mime_type="application/json",
        description="Area, power, timing, cell and netlist metrics of one stage.",
    )
    @_resource
    def qor_resource(flow_id: str, stage: str) -> str:
        return as_json(qor.qor_detail(ctx, flow_id, stage))

    @server.resource(
        "eda://image/{entity}/{name}/{flow_id}/{stage}",
        name="image",
        mime_type="image/png",
        description="Stored image rendered as a PNG of at most 512 px.",
    )
    @_resource
    def image_resource(entity: str, name: str, flow_id: str, stage: str) -> bytes:
        return images.render_image(ctx, entity=entity, name=name, flow_id=flow_id, stage=stage).png


def build_server(ctx: DatasetContext) -> MCPServer:
    """Create an ``MCPServer`` bound to ``ctx`` with all phase 1 tools and resources."""
    server = MCPServer(
        name=f"eda-schema-{ctx.pdk}",
        title=f"EDA-Schema ({ctx.pdk})",
        instructions=instructions_for(ctx),
        version=ctx.version,
    )
    for fn in TOOLS:
        doc = inspect.getdoc(fn) or ""
        server.add_tool(bind(ctx, fn), name=fn.__name__, description=doc, annotations=READ_ONLY)
    register_resources(server, ctx)
    return server


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Command-line arguments of ``eda-schema-mcp``."""
    parser = argparse.ArgumentParser(
        prog="eda-schema-mcp",
        description="Serve one per-PDK EDA-Schema dataset over the Model Context Protocol (stdio).",
    )
    parser.add_argument(
        "--dataset",
        default=os.environ.get(ENV_DATASET),
        help=f"Dataset root (default: ${ENV_DATASET}).",
    )
    parser.add_argument(
        "--max-rows", type=int, default=200, help="Hard cap for any 'limit' argument."
    )
    parser.add_argument(
        "--max-response-chars",
        type=int,
        default=40_000,
        help="Character budget for one tool response (about 4 chars per token).",
    )
    parser.add_argument("--precision", type=int, default=6, help="Significant digits for floats.")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (stderr).",
    )
    args = parser.parse_args(argv)
    if not args.dataset:
        parser.error(f"no dataset: pass --dataset or set {ENV_DATASET}")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``eda-schema-mcp``. Logs go to stderr; stdout carries MCP."""
    args = parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        ctx = DatasetContext(
            args.dataset,
            max_rows=args.max_rows,
            max_response_chars=args.max_response_chars,
            precision=args.precision,
        )
    except DatasetRootError as exc:
        print(f"eda-schema-mcp: {exc}", file=sys.stderr)
        return 2
    build_server(ctx).run("stdio")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
