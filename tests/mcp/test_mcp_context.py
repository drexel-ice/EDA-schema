# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/mcp/test_mcp_context.py
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

"""DatasetContext: PDK detection, catalogs, image index and lookups."""

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from eda_schema.mcp.context import STAGES, DatasetContext, parse_image_filename
from eda_schema.mcp.errors import DatasetRootError, McpInputError, not_found

from .conftest import FLOW, SAMPLE


# ----------------------------------------------------------------------
# Root validation and PDK identity
# ----------------------------------------------------------------------
def test_rejects_non_dataset_root(tmp_path):
    with pytest.raises(DatasetRootError, match="design_flows"):
        DatasetContext(tmp_path)


def test_pdk_from_dataloader_log(ctx):
    assert ctx.pdk == "sky130hd"
    assert ctx.pdk_source == "dataloader_log"
    assert ctx.root_id.startswith("sky130hd@")
    assert ctx.dataset_ref() == {"pdk": "sky130hd", "root_id": ctx.root_id}


@pytest.fixture()
def sample_copy(tmp_path) -> Path:
    dest = tmp_path / "ds"
    shutil.copytree(SAMPLE, dest)
    return dest


def test_pdk_from_manifest_wins(sample_copy):
    (sample_copy / "dataset.json").write_text(
        json.dumps({"pdk": "custom-pdk", "units": {"time": "ns"}, "schema_version": "9.9"})
    )
    c = DatasetContext(sample_copy)
    assert (c.pdk, c.pdk_source) == ("custom-pdk", "manifest")
    assert c.manifest["units"] == {"time": "ns"}


def test_bad_manifest_is_ignored(sample_copy):
    (sample_copy / "dataset.json").write_text("{not json")
    c = DatasetContext(sample_copy)
    assert c.manifest == {}
    assert c.pdk_source == "dataloader_log"


def test_non_dict_manifest_is_ignored(sample_copy):
    (sample_copy / "dataset.json").write_text("[1, 2]")
    assert DatasetContext(sample_copy).manifest == {}


def test_pdk_from_standard_cell_names(sample_copy):
    (sample_copy / "openroad_dataloader.log").unlink()
    c = DatasetContext(sample_copy)
    assert (c.pdk, c.pdk_source) == ("sky130hd", "standard_cell_names")


@pytest.mark.parametrize(
    "names, expected",
    [
        (["AND2_X1", "INV_X4", "DFF_X1"], "nangate45"),
        (["sg13g2_inv_1", "sg13g2_nand2_1"], "ihp-sg13g2"),
        (["sky130_fd_sc_hs__inv_1"], "sky130hs"),
    ],
)
def test_pdk_cell_prefixes(sample_copy, names, expected):
    (sample_copy / "openroad_dataloader.log").unlink()
    pd.DataFrame({"name": names}).to_parquet(sample_copy / "standard_cells" / "table.parquet")
    assert DatasetContext(sample_copy).pdk == expected


def test_pdk_unknown(sample_copy):
    (sample_copy / "openroad_dataloader.log").unlink()
    shutil.rmtree(sample_copy / "standard_cells")
    c = DatasetContext(sample_copy)
    assert (c.pdk, c.pdk_source) == ("unknown", "unknown")
    assert "standard_cells" not in c.entity_columns


def test_log_without_platform_falls_through(sample_copy):
    (sample_copy / "openroad_dataloader.log").write_text("no paths here\n")
    assert DatasetContext(sample_copy).pdk_source == "standard_cell_names"


# ----------------------------------------------------------------------
# Catalogs
# ----------------------------------------------------------------------
def test_entity_metadata(ctx):
    assert ctx.entity_rows["design_flows"] == 1
    assert ctx.entity_rows["timing_paths"] == 2340
    assert "graph_json" not in ctx.entity_columns.get("timing_paths", [])
    assert "standard_cell" in ctx.entity_columns["gates"]
    # Defined in GateEntity but absent from the sample table (mcp_plan.md 9.2).
    assert "total_power" not in ctx.entity_columns["gates"]


def test_flow_catalog(ctx):
    assert ctx.flow_ids == [FLOW]
    assert ctx.designs == ["gcd"]
    row = ctx.require_flow(FLOW)
    assert row["clock_period"] == 3.0 and row["design"] == "gcd"
    assert "core_utilization" in ctx.constraint_columns
    assert "flow_id" not in ctx.constraint_columns


def test_qor_catalog(ctx):
    assert len(ctx.qor) == 8
    assert ctx.stages_of(FLOW) == STAGES
    assert {"worst_slack", "total_power", "total_area", "no_of_cells"} <= set(ctx.metric_columns)
    assert "critical_path_startpoint" not in ctx.metric_columns  # not numeric
    assert ctx.metric_category["worst_slack"] == "timing"
    assert ctx.metric_category["utilization"] == "netlist"
    row = ctx.qor_row(FLOW, "final")
    assert row["stage"] == "final" and row["worst_slack"] == pytest.approx(-0.2732)


def test_image_index(ctx):
    refs = ctx.images_for(FLOW, "final")
    assert len(refs) == 26
    assert sum(len(v) for v in ctx.images.values()) == 98
    kinds = ctx.image_kinds()
    assert "routing_by_metal__met1" in kinds["netlists"]
    assert "ir_drop_vdd" in kinds["power_delivery_networks"]
    clock = [r for r in refs if r.entity == "clock_trees"]
    assert clock and all(r.clock_source == "clk" for r in clock)
    assert ctx.images_for(FLOW, "nope") == []


# ----------------------------------------------------------------------
# Lookups
# ----------------------------------------------------------------------
def test_require_flow_suggests(ctx):
    with pytest.raises(McpInputError, match="Closest matches: gcd-000001"):
        ctx.require_flow("gcd-00001")


def test_require_design(ctx):
    assert ctx.require_design("gcd") == "gcd"
    with pytest.raises(McpInputError, match="Unknown design"):
        ctx.require_design("nope")


def test_require_stage(ctx):
    assert ctx.require_stage(FLOW, "cts") == "cts"
    with pytest.raises(McpInputError, match="Closest matches: cts"):
        ctx.require_stage(FLOW, "cst")


def test_require_stage_missing_for_flow(multi_ctx):
    with pytest.raises(McpInputError, match="not available for flow"):
        multi_ctx.require_stage("gcd-000004", "final")


def test_require_metrics(ctx):
    assert ctx.require_metrics(["worst_slack"]) == ["worst_slack"]
    with pytest.raises(McpInputError, match="Unknown metric"):
        ctx.require_metrics(["worst_slak"])


def test_clamp_limit(tiny_ctx):
    assert tiny_ctx.clamp_limit(0) == 1
    assert tiny_ctx.clamp_limit(3) == 3
    assert tiny_ctx.clamp_limit(1000) == 5


def test_version(ctx):
    assert ctx.version != ""


# ----------------------------------------------------------------------
# Image filename parsing
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "filename, expected",
    [
        ("routing__flow_id=f-1__stage=cts.npz", ("routing", "f-1", "cts", {})),
        (
            "routing_by_metal__met2__flow_id=f-1__stage=final.npz",
            ("routing_by_metal__met2", "f-1", "final", {}),
        ),
        (
            "cell_placement__flow_id=f-1__stage=cts__clock_source=clk.npz",
            ("cell_placement", "f-1", "cts", {"clock_source": "clk"}),
        ),
    ],
)
def test_parse_image_filename(filename, expected):
    ref = parse_image_filename("netlists", Path(filename))
    assert (ref.name, ref.flow_id, ref.stage, ref.extra) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "routing__flow_id=f__stage=cts.npy",  # wrong suffix
        "routing__stage=cts.npz",  # no flow_id
        "flow_id=f__stage=cts.npz",  # no name
        "routing__flow_id=f__stage=cts__extra.npz",  # name part after keys
    ],
)
def test_parse_image_filename_rejects(filename):
    assert parse_image_filename("netlists", Path(filename)) is None


def test_not_found_without_close_match():
    err = not_found("design", "zzz", ["aaa", "bbb"])
    assert "Valid values: aaa, bbb" in str(err)


def test_not_found_lists_overflow():
    err = not_found("x", "zzz", [f"v{i}" for i in range(15)], show=3)
    assert "(+12 more)" in str(err)


def test_input_error_valid_values():
    assert "Valid values: a, b." in str(McpInputError("Bad.", ["a", "b"]))


def test_unreadable_log_falls_through(sample_copy):
    log = sample_copy / "openroad_dataloader.log"
    log.unlink()
    log.mkdir()  # opening a directory raises OSError
    assert DatasetContext(sample_copy).pdk_source == "standard_cell_names"


def test_missing_metric_table_is_skipped(sample_copy):
    shutil.rmtree(sample_copy / "power_metrics")
    c = DatasetContext(sample_copy)
    assert "total_power" not in c.metric_columns
    assert "worst_slack" in c.metric_columns
