# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/mcp/conftest.py
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

"""Fixtures for the MCP server tests.

* ``ctx``: the real sample dataset ``dataset/test`` (one gcd flow, SKY130).
* ``multi_ctx``: a copy of the sample with extra synthetic flows and a second
  design, written to a temporary directory. Only the small catalog tables are
  extended; element tables still hold gcd-000001 only. It exists because the
  sample has a single flow, which cannot exercise pagination, comparison or
  aggregation.
* ``tiny_ctx``: the sample with a very small response budget, to exercise
  truncation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("mcp", reason="install eda-schema[mcp] to run the MCP tests")

from eda_schema.mcp.context import DatasetContext

REPO = Path(__file__).resolve().parents[2]
SAMPLE = REPO / "dataset" / "test"
FLOW = "gcd-000001"

CATALOG_TABLES = [
    "design_flows",
    "constraints",
    "design_stages",
    "area_metrics",
    "cell_metrics",
    "power_metrics",
    "timing_metrics",
    "netlists",
]

# (flow_id, design, run_status, clock_period, core_utilization, aspect_ratio, slack_shift)
SYNTHETIC_FLOWS = [
    ("gcd-000002", "gcd", "Complete", 2.5, 0.4, 1.0, -0.20),
    ("gcd-000003", "gcd", "Complete", 3.5, 0.3, 0.5, +0.30),
    ("gcd-000004", "gcd", "Failed", 2.0, 0.5, 1.5, -0.50),
    ("aes-000001", "aes", "Complete", 1.5, 0.3, 1.0, +0.10),
]


def _write(df: pd.DataFrame, root: Path, entity: str) -> None:
    df.to_parquet(root / entity / "table.parquet", index=False)


def build_multi_flow_dataset(dest: Path) -> Path:
    """Copy the sample dataset to ``dest`` and add the synthetic flows."""
    shutil.copytree(SAMPLE, dest)
    for entity in CATALOG_TABLES:
        path = dest / entity / "table.parquet"
        base = pd.read_parquet(path)
        frames = [base]
        for flow_id, design, status, clk, util, ar, shift in SYNTHETIC_FLOWS:
            df = base.copy()
            df["flow_id"] = flow_id
            if entity == "design_flows":
                df["design"] = design
                df["run_status"] = status
            if entity == "constraints":
                df["clock_period"] = clk
                df["core_utilization"] = util
                df["aspect_ratio"] = ar
            if entity == "timing_metrics":
                df["worst_slack"] = df["worst_slack"] + shift
            if entity == "design_stages" and status == "Failed":
                df = df[df["stage"].isin(["floorplan", "global_place", "place_resized"])]
            if entity not in ("design_flows", "constraints") and status == "Failed":
                df = df[df["stage"].isin(["floorplan", "global_place", "place_resized"])]
            frames.append(df)
        _write(pd.concat(frames, ignore_index=True), dest, entity)
    return dest


@pytest.fixture(scope="session")
def ctx() -> DatasetContext:
    """Context over the real sample dataset."""
    return DatasetContext(SAMPLE)


@pytest.fixture(scope="session")
def multi_root(tmp_path_factory) -> Path:
    """Root of the synthetic multi-flow dataset."""
    return build_multi_flow_dataset(tmp_path_factory.mktemp("multi") / "dataset")


@pytest.fixture(scope="session")
def multi_ctx(multi_root) -> DatasetContext:
    """Context over the synthetic multi-flow dataset."""
    return DatasetContext(multi_root)


@pytest.fixture()
def tiny_ctx() -> DatasetContext:
    """Sample dataset with a 1,500-character response budget and 5-row cap."""
    return DatasetContext(SAMPLE, max_response_chars=1500, max_rows=5)
