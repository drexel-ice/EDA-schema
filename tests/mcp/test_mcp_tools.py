# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/mcp/test_mcp_tools.py
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

"""Tool functions called directly (without the MCP protocol).

Expected values come from the sample dataset ``dataset/test`` (gcd-000001,
SKY130); see mcp_plan.md section 2.
"""

import io
import itertools
import shutil

import pandas as pd
import pytest
from PIL import Image

from eda_schema.mcp.context import STAGES, DatasetContext
from eda_schema.mcp.errors import McpInputError
from eda_schema.mcp.tools import catalog, images, netlist, qor, timing
from eda_schema.mcp.tools.catalog import Range

from .conftest import FLOW, SAMPLE

WORST_START, WORST_END = "_381_/Q", "_395_/D"


# ----------------------------------------------------------------------
# catalog
# ----------------------------------------------------------------------
def test_get_dataset_info(ctx):
    out = catalog.get_dataset_info(ctx)
    data = out["data"]
    assert out["dataset"]["pdk"] == "sky130hd"
    assert data["counts"] == {
        "designs": 1,
        "flows": 1,
        "flow_run_status": {"Complete": 1},
        "stage_rows": 8,
    }
    assert data["stages"] == STAGES
    assert data["entities"]["gates"] == 4456
    assert "unknown" in data["units"]
    assert any("cross-PDK" in n for n in data["notes"])


def test_dataset_info_uses_manifest_units(tmp_path):
    dest = tmp_path / "ds"
    shutil.copytree(SAMPLE, dest)
    (dest / "dataset.json").write_text('{"pdk": "sky130hd", "units": {"time": "ns"}}')
    data = catalog.dataset_info(DatasetContext(dest))
    assert data["units"] == {"time": "ns"} and data["pdk_source"] == "manifest"


def test_list_designs(ctx, multi_ctx):
    assert catalog.list_designs(ctx)["data"] == [
        {
            "design": "gcd",
            "flows": 1,
            "run_status": {"Complete": 1},
            "clock_period": {"min": 3.0, "max": 3.0},
        }
    ]
    rows = catalog.list_designs(multi_ctx)["data"]
    assert [r["design"] for r in rows] == ["aes", "gcd"]
    assert rows[1]["flows"] == 4 and rows[1]["run_status"] == {"Complete": 3, "Failed": 1}


def test_list_flows_sample(ctx):
    out = catalog.list_flows(ctx)
    assert out["total"] == 1 and out["data"][0]["flow_id"] == FLOW
    assert out["data"][0]["core_utilization"] == 0.3


def test_list_flows_filters(multi_ctx):
    ids = lambda out: [r["flow_id"] for r in out["data"]]
    assert ids(catalog.list_flows(multi_ctx, design="aes")) == ["aes-000001"]
    assert ids(catalog.list_flows(multi_ctx, run_status="Failed")) == ["gcd-000004"]
    assert ids(catalog.list_flows(multi_ctx, clock_period=2.5)) == ["gcd-000002"]
    assert ids(catalog.list_flows(multi_ctx, clock_period=Range(min=2.5, max=3.0))) == [
        "gcd-000001",
        "gcd-000002",
    ]
    assert ids(catalog.list_flows(multi_ctx, core_utilization=Range(min=0.45))) == ["gcd-000004"]
    assert ids(catalog.list_flows(multi_ctx, aspect_ratio=Range(max=0.5))) == ["gcd-000003"]


def test_list_flows_sort_and_paginate(multi_ctx):
    first = catalog.list_flows(multi_ctx, sort_by="clock_period", descending=True, limit=2)
    assert [r["clock_period"] for r in first["data"]] == [3.5, 3.0]
    assert first["truncated"] is True and first["next_cursor"] == "2" and first["total"] == 5
    second = catalog.list_flows(
        multi_ctx, sort_by="clock_period", descending=True, limit=2, cursor=first["next_cursor"]
    )
    assert [r["clock_period"] for r in second["data"]] == [2.5, 2.0]
    last = catalog.list_flows(
        multi_ctx, sort_by="clock_period", descending=True, limit=2, cursor="4"
    )
    assert last["returned"] == 1 and last["truncated"] is False


def test_list_flows_errors(ctx):
    with pytest.raises(McpInputError, match="Unknown design"):
        catalog.list_flows(ctx, design="aes")


def test_list_flows_missing_constraint_column(tmp_path):
    dest = tmp_path / "ds"
    shutil.copytree(SAMPLE, dest)
    path = dest / "constraints" / "table.parquet"
    pd.read_parquet(path).drop(columns=["aspect_ratio"]).to_parquet(path, index=False)
    c = DatasetContext(dest)
    with pytest.raises(McpInputError, match="not recorded"):
        catalog.list_flows(c, aspect_ratio=1.0)
    with pytest.raises(McpInputError, match="Cannot sort"):
        catalog.list_flows(c, sort_by="aspect_ratio")
    with pytest.raises(McpInputError, match="Cannot group"):
        qor.aggregate_metrics(c, "worst_slack", group_by=["aspect_ratio"])


def test_get_flow(ctx):
    data = catalog.get_flow(ctx, FLOW)["data"]
    assert data["design"] == "gcd" and data["run_status"] == "Complete"
    assert data["constraints"]["clock_period"] == 3.0
    assert [s["stage"] for s in data["stages"]] == STAGES
    assert data["stages"][-1] == {"stage": "final", "status": "Complete", "images": 26}


def test_get_flow_unknown(ctx):
    with pytest.raises(McpInputError, match="gcd-000001"):
        catalog.get_flow(ctx, "gcd-1")


# ----------------------------------------------------------------------
# qor
# ----------------------------------------------------------------------
def test_get_qor(ctx):
    data = qor.get_qor(ctx, FLOW, "final")["data"]
    assert set(data["metrics"]) == {"area", "cell", "power", "timing", "netlist"}
    t = data["metrics"]["timing"]
    assert t["worst_slack"] == -0.2732
    assert t["critical_path_startpoint"] == "_381_/Q"
    assert data["metrics"]["netlist"]["no_of_cells"] == 1105


def test_get_qor_categories(ctx):
    data = qor.get_qor(ctx, FLOW, "cts", categories=["power"])["data"]
    assert list(data["metrics"]) == ["power"] and data["stage"] == "cts"


def test_get_qor_bad_stage(ctx):
    with pytest.raises(McpInputError, match="cts"):
        qor.get_qor(ctx, FLOW, "cst")


def test_get_stage_evolution_defaults(ctx):
    data = qor.get_stage_evolution(ctx, FLOW)["data"]
    assert [r["stage"] for r in data["stages"]] == STAGES
    assert data["metrics"][0] == "worst_slack"
    jump = data["largest_change"]["no_of_cells"]
    assert (jump["from_stage"], jump["to_stage"]) == ("global_route", "detailed_route")
    assert jump["delta"] == 652  # filler insertion


def test_get_stage_evolution_custom_metrics(ctx):
    data = qor.get_stage_evolution(ctx, FLOW, metrics=["total_negative_slack"])["data"]
    assert data["metrics"] == ["total_negative_slack"]
    assert set(data["stages"][0]) == {"stage", "stage_status", "total_negative_slack"}
    with pytest.raises(McpInputError, match="Unknown metric"):
        qor.get_stage_evolution(ctx, FLOW, metrics=["bogus"])


def test_get_stage_evolution_single_stage(multi_ctx):
    # The failed synthetic flow has 3 stages; a one-row metric has no delta.
    data = qor.get_stage_evolution(multi_ctx, "gcd-000004")["data"]
    assert len(data["stages"]) == 3


def test_get_stage_evolution_all_missing_metric(tmp_path):
    dest = tmp_path / "ds"
    shutil.copytree(SAMPLE, dest)
    path = dest / "power_metrics" / "table.parquet"
    df = pd.read_parquet(path)
    df["total_power"] = float("nan")
    df.to_parquet(path, index=False)
    data = qor.get_stage_evolution(
        DatasetContext(dest), FLOW, metrics=["total_power", "worst_slack"]
    )["data"]
    assert "total_power" not in data["largest_change"] and "worst_slack" in data["largest_change"]


def test_compare_flows(multi_ctx):
    out = qor.compare_flows(multi_ctx, ["gcd-000003", FLOW, "gcd-000004"], metrics=["worst_slack"])
    assert [r["flow_id"] for r in out["data"]] == ["gcd-000003", FLOW]  # caller order kept
    assert out["missing"] == ["gcd-000004"]  # failed flow has no final stage
    assert out["data"][0]["worst_slack"] == pytest.approx(-0.2732 + 0.30)
    assert out["data"][0]["clock_period"] == 3.5


def test_compare_flows_errors(ctx):
    with pytest.raises(McpInputError, match="Unknown stage"):
        qor.compare_flows(ctx, [FLOW], stage="nope")
    with pytest.raises(McpInputError, match="Unknown flow_id"):
        qor.compare_flows(ctx, ["nope"])


def test_aggregate_by_design(multi_ctx):
    out = qor.aggregate_metrics(
        multi_ctx, "worst_slack", group_by=["design"], aggs=["count", "min", "max"]
    )
    rows = {r["design"]: r for r in out["data"]}
    assert rows["gcd"]["count"] == 3  # failed flow excluded by default
    assert rows["gcd"]["min"] == pytest.approx(-0.4732)
    assert rows["gcd"]["max"] == pytest.approx(0.0268)
    assert out["stage"] == "final" and out["metric"] == "worst_slack"


def test_aggregate_include_incomplete_and_stage(multi_ctx):
    out = qor.aggregate_metrics(
        multi_ctx,
        "worst_slack",
        group_by=["design"],
        aggs=["count"],
        stage="floorplan",
        include_incomplete=True,
        design="gcd",
    )
    assert out["data"] == [{"design": "gcd", "count": 4}]


def test_aggregate_by_stage_and_constraint(multi_ctx):
    out = qor.aggregate_metrics(
        multi_ctx, "no_of_cells", group_by=["stage"], aggs=["median", "p10", "p90", "mean"]
    )
    assert [r["stage"] for r in out["data"]] == STAGES and out["stage"] is None
    by_clk = qor.aggregate_metrics(
        multi_ctx, "worst_slack", group_by=["clock_period"], aggs=["mean"]
    )
    assert [r["clock_period"] for r in by_clk["data"]] == [1.5, 2.5, 3.0, 3.5]


def test_aggregate_without_groups(multi_ctx):
    out = qor.aggregate_metrics(multi_ctx, "worst_slack", group_by=[], aggs=["count", "std"])
    assert out["data"][0]["count"] == 4


def test_aggregate_errors(ctx):
    with pytest.raises(McpInputError, match="Unknown metric"):
        qor.aggregate_metrics(ctx, "nope")
    with pytest.raises(McpInputError, match="Unknown stage"):
        qor.aggregate_metrics(ctx, "worst_slack", stage="nope")
    with pytest.raises(McpInputError, match="Unknown design"):
        qor.aggregate_metrics(ctx, "worst_slack", design="nope")


# ----------------------------------------------------------------------
# timing
# ----------------------------------------------------------------------
def test_timing_summary_setup(ctx):
    data = timing.get_timing_summary(ctx, FLOW, "final")["data"]
    assert data["reported"]["worst_slack"] == -0.2732
    assert data["reported"]["no_of_violating_endpoints"] == 96
    fp = data["from_paths"]
    assert fp["paths"] == 137 and fp["worst_slack"] == -0.2732
    assert fp["worst_path"] == {"startpoint": WORST_START, "endpoint": WORST_END}
    assert fp["violating_paths"] > 0 and fp["total_negative_slack"] < 0


def test_timing_summary_hold(ctx):
    data = timing.get_timing_summary(ctx, FLOW, "final", path_type="hold")["data"]
    assert data["reported"] is None
    assert data["from_paths"]["paths"] == 150 and data["from_paths"]["violating_paths"] == 0


def test_list_timing_paths(ctx):
    out = timing.list_timing_paths(ctx, FLOW, "final", limit=5)
    slacks = [r["slack"] for r in out["data"]]
    assert slacks == sorted(slacks) and slacks[0] == -0.2732
    assert out["total"] == 137 and out["next_cursor"] == "5"
    assert set(out["data"][0]) == set(timing.PATH_COLUMNS)


def test_list_timing_paths_options(ctx):
    viol = timing.list_timing_paths(ctx, FLOW, "final", only_violating=True, limit=200)
    assert viol["total"] == viol["returned"] and all(r["slack"] < 0 for r in viol["data"])
    best = timing.list_timing_paths(ctx, FLOW, "final", descending=True, limit=1)
    assert best["data"][0]["slack"] > 0
    by_pins = timing.list_timing_paths(
        ctx, FLOW, "cts", sort_by="no_of_pins", descending=True, limit=1
    )
    assert by_pins["stage"] == "cts"


def test_timing_requires_table(tmp_path):
    dest = tmp_path / "ds"
    shutil.copytree(SAMPLE, dest)
    shutil.rmtree(dest / "timing_paths")
    with pytest.raises(McpInputError, match="no timing_paths"):
        timing.list_timing_paths(DatasetContext(dest), FLOW)


def test_get_timing_path(ctx):
    data = timing.get_timing_path(ctx, FLOW, "final", WORST_START, WORST_END)["data"]
    assert data["path"]["slack"] == -0.2732 and data["path"]["no_of_pins"] == 28
    arcs = data["arcs"]
    assert data["totals"]["cell_arcs"] == 14 and data["totals"]["net_arcs"] == 14
    assert len(arcs) == 28
    # Arcs are ordered and chained pin to pin.
    for a, b in itertools.pairwise(arcs):
        assert a["to_pin"] == b["from_pin"]
    arrivals = [a["arrival_time"] for a in arcs]
    assert arrivals == sorted(arrivals)
    # The last arc is the endpoint flop's check arc; the net before it ends at D.
    assert arcs[-1] == {**arcs[-1], "kind": "cell", "name": "_395_", "to_pin": None}
    assert arcs[-2]["to_pin"] == WORST_END
    assert all("capacitance" in a for a in arcs if a["kind"] == "net")
    total = data["totals"]["cell_delay"] + data["totals"]["net_delay"]
    assert total == pytest.approx(arcs[-1]["arrival_time"], abs=0.01)


def test_get_timing_path_unknown(ctx):
    with pytest.raises(McpInputError, match="list_timing_paths"):
        timing.get_timing_path(ctx, FLOW, "final", "nope", WORST_END)


def test_get_timing_path_missing_graph_and_arcs(tmp_path):
    dest = tmp_path / "ds"
    shutil.copytree(SAMPLE, dest)
    shutil.rmtree(dest / "cell_arcs")
    c = DatasetContext(dest)
    data = timing.get_timing_path(c, FLOW, "final", WORST_START, WORST_END)["data"]
    assert all(a["delay"] is None for a in data["arcs"] if a["kind"] == "cell")
    assert data["totals"]["cell_delay"] == 0

    # A fresh copy: ParquetDB caches tables by path, so do not rewrite `dest`.
    dest = tmp_path / "ds2"
    shutil.copytree(SAMPLE, dest)
    graph = dest / "timing_paths" / "graph.parquet"
    df = pd.read_parquet(graph)
    df = df[
        ~(
            (df["stage"] == "final")
            & (df["startpoint"] == WORST_START)
            & (df["endpoint"] == WORST_END)
        )
    ]
    df.to_parquet(graph, index=False)
    with pytest.raises(McpInputError, match="graph of this path is not stored"):
        timing.get_timing_path(DatasetContext(dest), FLOW, "final", WORST_START, WORST_END)


def test_chain_fallbacks():
    assert timing._chain(["a", "b"], []) == ["a", "b"]
    assert timing._chain(["a", "b", "c"], [["a", "b"], ["b", "c"]]) == ["a", "b", "c"]
    # Two sources: not a chain, keep stored order.
    assert timing._chain(["a", "b", "c"], [["a", "c"], ["b", "c"]]) == ["a", "b", "c"]
    # A cycle back to the start stops the walk; incomplete order -> stored order.
    assert timing._chain(["s", "a", "b", "x"], [["s", "a"], ["a", "b"], ["b", "a"]]) == [
        "s",
        "a",
        "b",
        "x",
    ]
    # Self-loop at the end: walk stops, order is still complete.
    assert timing._chain(["a", "s"], [["s", "a"], ["a", "a"]]) == ["s", "a"]


# ----------------------------------------------------------------------
# netlist
# ----------------------------------------------------------------------
def test_get_netlist_summary(ctx):
    data = netlist.get_netlist_summary(ctx, FLOW, "final")["data"]
    assert data["netlist"]["no_of_cells"] == 1105 and data["netlist"]["width"] == 97.34
    assert data["cell_counts"]["no_of_fillers"] == 652
    assert data["area"]["total_area"] > 0
    assert data["distinct_standard_cells"] == 55
    top = data["top_standard_cells"]
    assert len(top) == 10 and top[0]["standard_cell"].startswith("sky130_fd_sc_hd__")
    assert [t["count"] for t in top] == sorted((t["count"] for t in top), reverse=True)


def test_get_netlist_summary_without_cells(ctx):
    data = netlist.get_netlist_summary(ctx, FLOW, "floorplan", top_cells=0)["data"]
    assert "top_standard_cells" not in data and data["netlist"]["no_of_cells"] == 312


# ----------------------------------------------------------------------
# images
# ----------------------------------------------------------------------
def test_list_images(ctx):
    data = images.list_images(ctx, FLOW, "final")["data"]["images"]
    assert "routing" in data["netlists"]
    assert {"name": "routing", "clock_source": "clk"} in data["clock_trees"]
    assert "ir_drop_vdd" in data["power_delivery_networks"]
    assert "rudy_net" in data["routability_metrics"]


def test_render_binary(ctx):
    res = images.render_image(ctx, "netlists", "routing", FLOW, "final", max_px=256)
    with Image.open(io.BytesIO(res.png)) as img:
        assert max(img.size) <= 256
    assert res.info["kind"] == "binary" and res.info["shape"] == [695, 695]
    assert res.info["dataset"]["pdk"] == "sky130hd"


def test_render_scalar_and_clock(ctx):
    res = images.render_image(ctx, "power_delivery_networks", "ir_drop_vdd", FLOW, "final")
    assert res.info["kind"] == "scalar" and res.info["shape"] == [14, 14]
    clk = images.render_image(ctx, "clock_trees", "routing", FLOW, "final", clock_source="clk")
    assert clk.info["clock_source"] == "clk"
    auto = images.render_image(ctx, "clock_trees", "routing", FLOW, "final")
    assert auto.info["clock_source"] == "clk"  # single clock: picked automatically


def test_render_errors(ctx):
    with pytest.raises(McpInputError, match="image entity"):
        images.render_image(ctx, "gates", "routing", FLOW)
    with pytest.raises(McpInputError, match="netlists image"):
        images.render_image(ctx, "netlists", "routng", FLOW)
    with pytest.raises(McpInputError, match="clock_source"):
        images.render_image(ctx, "clock_trees", "routing", FLOW, clock_source="clk2")
    with pytest.raises(McpInputError, match="colormap"):
        images.render_image(ctx, "power_delivery_networks", "ir_drop_vdd", FLOW, colormap="zzz")


def test_render_multiple_clock_sources(tmp_path):
    dest = tmp_path / "ds"
    shutil.copytree(SAMPLE, dest)
    src = (
        dest
        / "clock_trees"
        / "images"
        / f"routing__flow_id={FLOW}__stage=final__clock_source=clk.npz"
    )
    shutil.copy(src, src.with_name(src.name.replace("clock_source=clk", "clock_source=clk2")))
    c = DatasetContext(dest)
    with pytest.raises(McpInputError, match="several clock sources"):
        images.render_image(c, "clock_trees", "routing", FLOW)
    assert (
        images.render_image(c, "clock_trees", "routing", FLOW, clock_source="clk2").info[
            "clock_source"
        ]
        == "clk2"
    )
