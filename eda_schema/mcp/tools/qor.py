# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/tools/qor.py
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

"""QoR metric tools (mcp_plan.md section 6.3).

All of these run on the in-memory QoR catalog (one row per flow and stage),
so they never touch the large element tables.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

import pandas as pd
from pydantic import Field

from eda_schema.mcp.context import QOR_TABLES, STAGES, DatasetContext
from eda_schema.mcp.envelope import ok, paged, records
from eda_schema.mcp.errors import McpInputError, not_found

DEFAULT_METRICS: list[str] = [
    "worst_slack",
    "total_negative_slack",
    "no_of_violating_endpoints",
    "total_power",
    "total_area",
    "no_of_cells",
    "utilization",
]
"""Metrics used when a tool's ``metrics`` argument is omitted."""

Category = Literal["area", "cell", "power", "timing", "netlist"]
GroupBy = Literal[
    "design", "stage", "run_status", "clock_period", "core_utilization", "aspect_ratio"
]
Agg = Literal["count", "mean", "std", "min", "max", "median", "p10", "p90"]

FlowId = Annotated[str, Field(description="Flow id, e.g. 'gcd-000001'.")]
Stage = Annotated[str, Field(description=f"Design stage, one of: {', '.join(STAGES)}.")]
Metrics = Annotated[
    list[str] | None,
    Field(description="QoR metric column names (see eda://schema). Omit for a default set."),
]


def _default_metrics(ctx: DatasetContext) -> list[str]:
    return [m for m in DEFAULT_METRICS if m in ctx.metric_columns]


def qor_detail(ctx: DatasetContext, flow_id: str, stage: str, categories=None) -> dict[str, Any]:
    """Plain dict of one stage's QoR, grouped by category."""
    ctx.require_flow(flow_id)
    ctx.require_stage(flow_id, stage)
    row = ctx.qor_row(flow_id, stage)
    wanted = list(categories) if categories else list(QOR_TABLES)
    grouped: dict[str, dict[str, Any]] = {cat: {} for cat in wanted}
    for col, cat in ctx.metric_category.items():
        if cat in grouped and col in row:
            grouped[cat][col] = row[col]
    return {
        "flow_id": flow_id,
        "stage": stage,
        "stage_status": row.get("stage_status"),
        "metrics": grouped,
    }


def get_qor(
    ctx: DatasetContext,
    flow_id: FlowId,
    stage: Stage = "final",
    categories: Annotated[
        list[Category] | None,
        Field(description="Subset of metric categories. Omit for all."),
    ] = None,
) -> dict[str, Any]:
    """Get the quality-of-results metrics of one flow at one stage.

    Metrics are grouped into area, cell counts, power, timing (setup WNS/TNS,
    critical start/end points, violating endpoints) and netlist summary
    (cells, nets, pins, utilization, die size).
    """
    return ok(ctx, qor_detail(ctx, flow_id, stage, categories))


def get_stage_evolution(
    ctx: DatasetContext,
    flow_id: FlowId,
    metrics: Metrics = None,
) -> dict[str, Any]:
    """Show how metrics change across the design stages of one flow.

    Returns one row per stage plus, for each metric, the stage transition
    with the largest absolute change.
    """
    ctx.require_flow(flow_id)
    metrics = ctx.require_metrics(metrics) if metrics else _default_metrics(ctx)
    df = ctx.qor[ctx.qor["flow_id"] == flow_id].sort_values("stage")
    df = df.assign(stage=df["stage"].astype(str))
    rows = records(df, ["stage", "stage_status", *metrics])

    biggest: dict[str, Any] = {}
    for metric in metrics:
        series = df[metric].astype(float).reset_index(drop=True)
        deltas = series.diff()
        if deltas.dropna().empty:
            continue
        idx = int(deltas.abs().idxmax())
        biggest[metric] = {
            "from_stage": df["stage"].iloc[idx - 1],
            "to_stage": df["stage"].iloc[idx],
            "delta": deltas.iloc[idx],
            "from_value": series.iloc[idx - 1],
            "to_value": series.iloc[idx],
        }
    return ok(
        ctx, {"flow_id": flow_id, "metrics": metrics, "stages": rows, "largest_change": biggest}
    )


def compare_flows(
    ctx: DatasetContext,
    flow_ids: Annotated[
        list[str], Field(min_length=1, max_length=20, description="1-20 flow ids.")
    ],
    stage: Stage = "final",
    metrics: Metrics = None,
) -> dict[str, Any]:
    """Compare several flows side by side at one stage.

    Each row holds the flow's design, its constraints and the requested
    metrics. Flows without the requested stage are reported in ``missing``.
    """
    if stage not in STAGES:
        raise not_found("stage", stage, STAGES)
    for fid in flow_ids:
        ctx.require_flow(fid)
    metrics = ctx.require_metrics(metrics) if metrics else _default_metrics(ctx)

    qor = ctx.qor[(ctx.qor["flow_id"].isin(flow_ids)) & (ctx.qor["stage"] == stage)]
    merged = ctx.flows[ctx.flows["flow_id"].isin(flow_ids)].merge(
        qor[["flow_id", *metrics]], on="flow_id", how="left"
    )
    order = {fid: i for i, fid in enumerate(flow_ids)}
    merged = merged.sort_values("flow_id", key=lambda s: s.map(order))
    present = set(qor["flow_id"])
    cols = ["flow_id", "design", *ctx.constraint_columns, *metrics]
    rows = records(merged[merged["flow_id"].isin(present)], cols)
    missing = [fid for fid in flow_ids if fid not in present]
    return paged(ctx, rows, total=len(rows), stage=stage, metrics=metrics, missing=missing)


def _agg_fn(name: str):
    if name == "p10":
        return lambda s: s.quantile(0.10)
    if name == "p90":
        return lambda s: s.quantile(0.90)
    return name


def aggregate_metrics(
    ctx: DatasetContext,
    metric: Annotated[str, Field(description="QoR metric column, e.g. 'worst_slack'.")],
    group_by: Annotated[list[GroupBy], Field(description="Columns to group by.")] = ("design",),
    aggs: Annotated[list[Agg], Field(min_length=1, description="Statistics to compute.")] = (
        "count",
        "mean",
        "min",
        "max",
        "std",
    ),
    stage: Annotated[
        str, Field(description="Stage to aggregate (ignored when grouping by stage).")
    ] = "final",
    design: Annotated[str | None, Field(description="Only flows of this design.")] = None,
    include_incomplete: Annotated[
        bool, Field(description="Include flows whose run_status is not 'Complete'.")
    ] = False,
) -> dict[str, Any]:
    """Compute grouped statistics of one metric over many flows.

    Group by design, stage, run status or a swept constraint (clock period,
    core utilization, aspect ratio). Statistics are computed on the server, so
    the response stays small even across the whole dataset.
    """
    ctx.require_metrics([metric])
    group_by = list(dict.fromkeys(group_by))
    if "stage" not in group_by and stage not in STAGES:
        raise not_found("stage", stage, STAGES)

    flows = ctx.flows
    if design is not None:
        ctx.require_design(design)
        flows = flows[flows["design"] == design]
    if not include_incomplete and "run_status" in flows:
        flows = flows[flows["run_status"] == "Complete"]

    qor = ctx.qor[ctx.qor["flow_id"].isin(flows["flow_id"])]
    if "stage" not in group_by:
        qor = qor[qor["stage"] == stage]
    df = qor[["flow_id", "stage", metric]].merge(flows, on="flow_id", how="left")
    for col in group_by:
        if col not in df.columns:
            raise McpInputError(f"Cannot group by {col!r}; it is not recorded in this dataset.")

    if group_by:
        grouped = df.groupby(group_by, observed=True, sort=True)[metric]
        table = grouped.agg([_agg_fn(a) for a in aggs])
        table.columns = list(aggs)
        table = table.reset_index()
    else:
        series = df[metric]
        table = pd.DataFrame([{a: series.agg(_agg_fn(a)) for a in aggs}])
    if "stage" in table.columns:
        table["stage"] = table["stage"].astype(str)

    limit = ctx.max_rows
    rows = records(table.head(limit))
    return paged(
        ctx,
        rows,
        total=len(table),
        metric=metric,
        stage=None if "stage" in group_by else stage,
        group_by=group_by,
        hint="Too many groups; add a design filter or group by fewer columns.",
    )
