# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/tools/netlist.py
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

"""Netlist summary tool (mcp_plan.md section 6.5, phase 1 subset)."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from eda_schema.mcp.context import DatasetContext
from eda_schema.mcp.envelope import ok
from eda_schema.mcp.tools.qor import FlowId, Stage

NETLIST_FIELDS = [
    "no_of_inputs",
    "no_of_outputs",
    "no_of_cells",
    "no_of_nets",
    "no_of_pins",
    "utilization",
    "width",
    "height",
    "total_wirelength",
    "total_hpwl",
]


def get_netlist_summary(
    ctx: DatasetContext,
    flow_id: FlowId,
    stage: Stage = "final",
    top_cells: Annotated[
        int,
        Field(ge=0, le=50, description="How many most-used standard cells to list (0 to skip)."),
    ] = 10,
) -> dict[str, Any]:
    """Summarize the netlist of one flow at one stage.

    Returns IO, cell, net and pin counts, utilization, die width/height,
    cell-type counts, area totals, and the most-used standard cells. The
    netlist graph itself is never returned (it is tens of thousands of tokens
    even for the smallest design).
    """
    ctx.require_flow(flow_id)
    ctx.require_stage(flow_id, stage)
    row = ctx.qor_row(flow_id, stage)
    netlist = {k: row[k] for k in NETLIST_FIELDS if k in row}
    cell_counts = {k: v for k, v in row.items() if ctx.metric_category.get(k) == "cell"}
    area = {
        k: row[k]
        for k in ("cell_area", "total_area", "combinational_cell_area", "sequential_cell_area")
        if k in row
    }

    data: dict[str, Any] = {
        "flow_id": flow_id,
        "stage": stage,
        "netlist": netlist,
        "cell_counts": cell_counts,
        "area": area,
    }
    if top_cells and "gates" in ctx.entity_columns:
        gates = ctx.db.get_table_data(
            "gates", columns=["standard_cell"], flow_id=flow_id, stage=stage
        )
        counts = gates["standard_cell"].value_counts()
        data["distinct_standard_cells"] = int(counts.size)
        data["top_standard_cells"] = [
            {"standard_cell": name, "count": int(n)} for name, n in counts.head(top_cells).items()
        ]
    return ok(ctx, data)
