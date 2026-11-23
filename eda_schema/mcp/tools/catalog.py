# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/tools/catalog.py
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

"""Session, discovery and catalog tools (mcp_plan.md sections 6.0 and 6.2)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from eda_schema.mcp.context import STAGES, DatasetContext
from eda_schema.mcp.envelope import ok, paged, parse_cursor, records
from eda_schema.mcp.errors import McpInputError

CROSS_PDK_NOTE = (
    "This server serves a single PDK. Do not compare its numbers with other "
    "eda-schema servers: cross-PDK comparison is not supported (units, libraries "
    "and timing scales differ)."
)


class Range(BaseModel):
    """Inclusive numeric range; either bound may be omitted."""

    min: float | None = None
    max: float | None = None


NumberOrRange = Annotated[
    float | Range | None,
    Field(description='Exact value (e.g. 1.5) or a range {"min": 1.0, "max": 2.0}.'),
]


def _apply_numeric_filter(
    df: pd.DataFrame, column: str, value: float | Range | None
) -> pd.DataFrame:
    if value is None:
        return df
    if column not in df.columns:
        raise McpInputError(f"Constraint {column!r} is not recorded in this dataset.")
    col = df[column]
    if isinstance(value, Range):
        mask = pd.Series(True, index=df.index)
        if value.min is not None:
            mask &= col >= value.min
        if value.max is not None:
            mask &= col <= value.max
        return df[mask]
    return df[np.isclose(col.astype(float), float(value), rtol=1e-9, atol=1e-12)]


# ----------------------------------------------------------------------
# 6.0 Session and dataset
# ----------------------------------------------------------------------
def dataset_info(ctx: DatasetContext) -> dict[str, Any]:
    """Plain dict describing the dataset (shared by the tool and the resource)."""
    status = ctx.flows["run_status"].value_counts().to_dict() if "run_status" in ctx.flows else {}
    return {
        "pdk": ctx.pdk,
        "pdk_source": ctx.pdk_source,
        "root_id": ctx.root_id,
        "root": str(ctx.root),
        "schema_version": ctx.manifest.get("schema_version", ctx.version),
        "package_version": ctx.version,
        "units": ctx.manifest.get("units")
        or "unknown (no dataset.json manifest; values are in the dataset's native units)",
        "counts": {
            "designs": len(ctx.designs),
            "flows": len(ctx.flows),
            "flow_run_status": status,
            "stage_rows": len(ctx.qor),
        },
        "designs": ctx.designs if len(ctx.designs) <= 50 else ctx.designs[:50],
        "stages": STAGES,
        "constraints": ctx.constraint_columns,
        "entities": dict(sorted(ctx.entity_rows.items())),
        "image_kinds": ctx.image_kinds(),
        "limits": {
            "max_rows": ctx.max_rows,
            "max_response_chars": ctx.max_response_chars,
            "float_significant_digits": ctx.precision,
        },
        "notes": [CROSS_PDK_NOTE],
    }


def get_dataset_info(ctx: DatasetContext) -> dict[str, Any]:
    """Describe the dataset this session is bound to.

    Returns the PDK, dataset identity, units, flow/design/stage counts, the
    entities and image kinds present, and the response limits. Call this first.
    """
    return ok(ctx, dataset_info(ctx))


# ----------------------------------------------------------------------
# 6.2 Discovery and catalog
# ----------------------------------------------------------------------
def designs_table(ctx: DatasetContext) -> list[dict[str, Any]]:
    """One summary row per design."""
    flows = ctx.flows
    rows: list[dict[str, Any]] = []
    for design, group in flows.groupby("design", sort=True):
        row: dict[str, Any] = {"design": design, "flows": len(group)}
        if "run_status" in group:
            row["run_status"] = group["run_status"].value_counts().to_dict()
        if "clock_period" in group:
            row["clock_period"] = {
                "min": group["clock_period"].min(),
                "max": group["clock_period"].max(),
            }
        rows.append(row)
    return rows


def list_designs(ctx: DatasetContext) -> dict[str, Any]:
    """List the designs (benchmark circuits) in this dataset.

    Each row gives the number of flows, their run-status breakdown and the
    swept clock-period range.
    """
    rows = designs_table(ctx)
    return paged(ctx, rows, total=len(rows))


FlowSort = Literal[
    "flow_id",
    "design",
    "clock_period",
    "core_utilization",
    "aspect_ratio",
    "clock_uncertainty",
]


def list_flows(
    ctx: DatasetContext,
    design: Annotated[str | None, Field(description="Only flows of this design.")] = None,
    run_status: Annotated[
        str | None, Field(description="Only flows with this run status, e.g. 'Complete'.")
    ] = None,
    clock_period: NumberOrRange = None,
    core_utilization: NumberOrRange = None,
    aspect_ratio: NumberOrRange = None,
    sort_by: Annotated[FlowSort, Field(description="Column to sort by.")] = "flow_id",
    descending: bool = False,
    limit: Annotated[int, Field(ge=1, description="Rows per page (capped by the server).")] = 50,
    cursor: Annotated[
        str | None, Field(description="next_cursor from a previous call, to get the next page.")
    ] = None,
) -> dict[str, Any]:
    """List flows (one implementation run each) with their design constraints.

    Filter by design, run status and constraint values or ranges; results are
    paginated. Use get_flow for one flow's detail and compare_flows or
    aggregate_metrics to analyse QoR across flows.
    """
    df = ctx.flows
    if design is not None:
        ctx.require_design(design)
        df = df[df["design"] == design]
    if run_status is not None:
        df = df[df["run_status"] == run_status]
    df = _apply_numeric_filter(df, "clock_period", clock_period)
    df = _apply_numeric_filter(df, "core_utilization", core_utilization)
    df = _apply_numeric_filter(df, "aspect_ratio", aspect_ratio)
    if sort_by not in df.columns:
        raise McpInputError(f"Cannot sort by {sort_by!r}; it is not recorded in this dataset.")
    df = df.sort_values([sort_by, "flow_id"], ascending=not descending, kind="stable")

    offset = parse_cursor(cursor)
    limit = ctx.clamp_limit(limit)
    page = df.iloc[offset : offset + limit]
    return paged(
        ctx,
        records(page),
        total=len(df),
        offset=offset,
        hint="Narrow with design/constraint filters, or use aggregate_metrics for statistics.",
    )


def flow_detail(ctx: DatasetContext, flow_id: str) -> dict[str, Any]:
    """Plain dict for one flow (shared by the tool and the resource)."""
    flow = ctx.require_flow(flow_id)
    constraints = {c: flow.get(c) for c in ctx.constraint_columns}
    stage_rows = ctx.qor[ctx.qor["flow_id"] == flow_id]
    stages = []
    for _, row in stage_rows.iterrows():
        stage = str(row["stage"])
        stages.append(
            {
                "stage": stage,
                "status": row.get("stage_status"),
                "images": len(ctx.images_for(flow_id, stage)),
            }
        )
    return {
        "flow_id": flow_id,
        "design": flow.get("design"),
        "run_status": flow.get("run_status"),
        "constraints": constraints,
        "stages": stages,
    }


def get_flow(
    ctx: DatasetContext,
    flow_id: Annotated[str, Field(description="Flow id, e.g. 'gcd-000001'.")],
) -> dict[str, Any]:
    """Get one flow: design, run status, constraints and per-stage status.

    Each stage lists its status and how many images are stored for it.
    """
    return ok(ctx, flow_detail(ctx, flow_id))
