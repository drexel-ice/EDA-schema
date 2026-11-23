# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/tools/timing.py
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

"""Timing tools (mcp_plan.md section 6.4, phase 1 subset).

``timing_paths``, ``cell_arcs`` and ``net_arcs`` are element tables: they are
always read filtered by ``flow_id`` and ``stage`` (and by the path key for a
single path), never whole.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Annotated, Any, Literal

import pandas as pd
from pydantic import Field

from eda_schema.errors import DataNotFoundError
from eda_schema.mcp.context import DatasetContext
from eda_schema.mcp.envelope import ok, paged, parse_cursor, records
from eda_schema.mcp.errors import McpInputError
from eda_schema.mcp.tools.qor import FlowId, Stage

PathType = Annotated[Literal["setup", "hold"], Field(description="Timing check type.")]
PathSort = Literal["slack", "arrival_time", "required_time", "no_of_pins"]

PATH_COLUMNS = [
    "startpoint",
    "endpoint",
    "path_type",
    "slack",
    "arrival_time",
    "required_time",
    "no_of_pins",
    "is_critical_path",
]
TIMING_REPORTED = [
    "worst_slack",
    "total_negative_slack",
    "critical_path_startpoint",
    "critical_path_endpoint",
    "worst_arrival_time",
    "worst_required_time",
    "no_of_endpoints",
    "no_of_violating_endpoints",
]


def _paths(ctx: DatasetContext, flow_id: str, stage: str, path_type: str) -> pd.DataFrame:
    ctx.require_flow(flow_id)
    ctx.require_stage(flow_id, stage)
    if "timing_paths" not in ctx.entity_columns:
        raise McpInputError("This dataset has no timing_paths table.")
    return ctx.db.get_table_data("timing_paths", flow_id=flow_id, stage=stage, path_type=path_type)


def get_timing_summary(
    ctx: DatasetContext,
    flow_id: FlowId,
    stage: Stage = "final",
    path_type: PathType = "setup",
) -> dict[str, Any]:
    """Summarize timing of one flow at one stage.

    ``reported`` holds the STA summary from timing_metrics (setup analysis:
    WNS, TNS, critical start/end points, endpoint counts). ``from_paths`` is
    computed from the stored timing paths of the requested ``path_type``
    (worst slack, TNS, violating paths and slack percentiles), so it is also
    available for hold.
    """
    df = _paths(ctx, flow_id, stage, path_type)
    row = ctx.qor_row(flow_id, stage)
    reported = (
        {k: row.get(k) for k in TIMING_REPORTED if k in row} if path_type == "setup" else None
    )

    from_paths: dict[str, Any] = {"paths": len(df)}
    if not df.empty:
        slack = df["slack"].astype(float)
        worst = df.loc[slack.idxmin()]
        from_paths.update(
            worst_slack=slack.min(),
            total_negative_slack=slack[slack < 0].sum(),
            violating_paths=int((slack < 0).sum()),
            worst_path={"startpoint": worst["startpoint"], "endpoint": worst["endpoint"]},
            slack_percentiles={
                "p0": slack.min(),
                "p10": slack.quantile(0.10),
                "p50": slack.quantile(0.50),
                "p90": slack.quantile(0.90),
            },
        )
    return ok(
        ctx,
        {
            "flow_id": flow_id,
            "stage": stage,
            "path_type": path_type,
            "reported": reported,
            "from_paths": from_paths,
        },
    )


def list_timing_paths(
    ctx: DatasetContext,
    flow_id: FlowId,
    stage: Stage = "final",
    path_type: PathType = "setup",
    only_violating: Annotated[bool, Field(description="Only paths with negative slack.")] = False,
    sort_by: Annotated[PathSort, Field(description="Column to sort by.")] = "slack",
    descending: Annotated[
        bool, Field(description="Sort descending (default: worst slack first).")
    ] = False,
    limit: Annotated[int, Field(ge=1, description="Rows per page (capped by the server).")] = 20,
    cursor: Annotated[str | None, Field(description="next_cursor from a previous call.")] = None,
) -> dict[str, Any]:
    """List timing paths of one flow at one stage, worst slack first by default.

    Rows contain start/end points, slack, arrival/required time and pin count,
    but not the path itself; call get_timing_path for one path's arcs.
    Large designs have thousands of paths per stage, so results are paginated.
    """
    df = _paths(ctx, flow_id, stage, path_type)
    if only_violating:
        df = df[df["slack"] < 0]
    df = df.sort_values(
        [sort_by, "startpoint", "endpoint"], ascending=not descending, kind="stable"
    )
    offset = parse_cursor(cursor)
    limit = ctx.clamp_limit(limit)
    page = df.iloc[offset : offset + limit]
    return paged(
        ctx,
        records(page, PATH_COLUMNS),
        total=len(df),
        offset=offset,
        flow_id=flow_id,
        stage=stage,
        hint="Use get_timing_summary for the distribution instead of paging through all paths.",
    )


def _chain(nodes: list[str], edges: list[list[str]]) -> list[str]:
    """Order path nodes by following edges from the source (falls back to list order)."""
    if not edges:
        return list(nodes)
    succ: dict[str, list[str]] = defaultdict(list)
    indeg: dict[str, int] = {n: 0 for n in nodes}
    for a, b in edges:
        succ[a].append(b)
        indeg[b] = indeg.get(b, 0) + 1
        indeg.setdefault(a, 0)
    start = [n for n in nodes if indeg.get(n, 0) == 0]
    if len(start) != 1:
        return list(nodes)
    order, seen = [start[0]], {start[0]}
    while succ.get(order[-1]):
        nxt = next((n for n in succ[order[-1]] if n not in seen), None)
        if nxt is None:
            break
        order.append(nxt)
        seen.add(nxt)
    return order if len(order) == len(set(nodes)) else list(nodes)


def get_timing_path(
    ctx: DatasetContext,
    flow_id: FlowId,
    stage: Annotated[str, Field(description="Design stage.")],
    startpoint: Annotated[str, Field(description="Path startpoint pin, e.g. '_381_/Q'.")],
    endpoint: Annotated[str, Field(description="Path endpoint pin, e.g. '_395_/D'.")],
    path_type: PathType = "setup",
) -> dict[str, Any]:
    """Get one timing path as an ordered list of cell and net arcs.

    Each arc gives its from/to pins, delay, arrival time and slew (plus
    capacitance for net arcs). Totals split the path delay into cell and net
    delay. The path starts in the launch clock network and ends with the
    endpoint cell's check arc (its ``to_pin`` is null).
    """
    ctx.require_flow(flow_id)
    ctx.require_stage(flow_id, stage)
    keys = {
        "flow_id": flow_id,
        "stage": stage,
        "startpoint": startpoint,
        "endpoint": endpoint,
        "path_type": path_type,
    }
    summary = ctx.db.get_table_data("timing_paths", **keys)
    if summary.empty:
        raise McpInputError(
            f"No {path_type} path from {startpoint!r} to {endpoint!r} in {flow_id} at {stage}. "
            "Use list_timing_paths to find valid start/end points."
        )
    try:
        graph = ctx.db.get_graph_data("timing_paths", **keys)
    except DataNotFoundError as exc:
        raise McpInputError(f"The graph of this path is not stored: {exc}") from exc

    nodes: list[str] = graph.get("nodes", [])
    types = dict(zip(nodes, graph.get("node_types", [])))
    order = _chain(nodes, graph.get("edges", []))

    arc_rows: dict[str, dict[str, deque[dict[str, Any]]]] = {"CELL_ARC": {}, "NET_ARC": {}}
    for kind, entity_name, name_col in (
        ("CELL_ARC", "cell_arcs", "gate_name"),
        ("NET_ARC", "net_arcs", "net_name"),
    ):
        if entity_name not in ctx.entity_columns:
            continue
        df = ctx.db.get_table_data(entity_name, **keys).sort_values("arrival_time", kind="stable")
        buckets: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
        for row in records(df):
            buckets[row[name_col]].append(row)
        arc_rows[kind] = buckets

    arcs: list[dict[str, Any]] = []
    for i, node in enumerate(order):
        kind = types.get(node)
        if kind not in arc_rows:
            continue
        row = arc_rows[kind].get(node)
        data = row.popleft() if row else {}
        arc = {
            "kind": "cell" if kind == "CELL_ARC" else "net",
            "name": node,
            "from_pin": order[i - 1] if i > 0 else None,
            "to_pin": order[i + 1] if i + 1 < len(order) else None,
            "delay": data.get("delay"),
            "arrival_time": data.get("arrival_time"),
            "slew": data.get("slew"),
        }
        if kind == "NET_ARC":
            arc["capacitance"] = data.get("capacitance")
        arcs.append(arc)

    cell_delay = sum(a["delay"] or 0.0 for a in arcs if a["kind"] == "cell")
    net_delay = sum(a["delay"] or 0.0 for a in arcs if a["kind"] == "net")
    head = records(summary, PATH_COLUMNS)[0]
    return ok(
        ctx,
        {
            "flow_id": flow_id,
            "stage": stage,
            "path": head,
            "totals": {
                "cell_delay": cell_delay,
                "net_delay": net_delay,
                "cell_arcs": sum(1 for a in arcs if a["kind"] == "cell"),
                "net_arcs": sum(1 for a in arcs if a["kind"] == "net"),
            },
            "arcs": arcs,
        },
    )
