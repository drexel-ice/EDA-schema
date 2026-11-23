# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/mcp/test_mcp_envelope.py
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

"""Response envelope: JSON cleaning, rounding, paging and the size budget."""

import json
import math

import numpy as np
import pandas as pd
import pytest

from eda_schema.mcp.envelope import (
    Envelope,
    clean,
    dumps,
    ok,
    paged,
    parse_cursor,
    records,
    round_sig,
)
from eda_schema.mcp.errors import McpInputError


@pytest.mark.parametrize(
    "value, digits, expected",
    [
        (123456.789, 4, 123500.0),
        (-0.000123456, 3, -0.000123),
        (0.0, 4, 0.0),
        (2.0, 6, 2.0),
    ],
)
def test_round_sig(value, digits, expected):
    assert round_sig(value, digits) == pytest.approx(expected)


def test_round_sig_passes_non_finite():
    assert math.isinf(round_sig(float("inf"), 3))


def test_clean_handles_numpy_pandas_and_specials():
    raw = {
        "np_int": np.int64(3),
        "np_float": np.float32(1.5),
        "nan": float("nan"),
        "pinf": float("inf"),
        "ninf": -np.inf,
        "na": pd.NA,
        "nat": pd.NaT,
        "bool": np.bool_(True),
        "arr": np.array([1.23456789, 2.0]),
        "tuple": (1, "a"),
        "ts": pd.Timestamp("2026-01-15T03:23:47"),
        "obj": object,
        7: "int key",
    }
    out = clean(raw, digits=3)
    assert out["np_int"] == 3 and isinstance(out["np_int"], int)
    assert out["np_float"] == 1.5
    assert out["nan"] is None and out["na"] is None and out["nat"] is None
    assert out["pinf"] == "inf" and out["ninf"] == "-inf"
    assert out["bool"] is True
    assert out["arr"] == [1.23, 2.0]
    assert out["tuple"] == [1, "a"]
    assert out["ts"].startswith("2026-01-15T03:23:47")
    assert out["7"] == "int key"
    assert isinstance(out["obj"], str)
    json.dumps(out, allow_nan=False)  # must be strict JSON


def test_records_selects_existing_columns():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert records(df, ["b", "missing"]) == [{"b": 3}, {"b": 4}]
    assert records(df) == [{"a": 1, "b": 3}, {"a": 2, "b": 4}]


def test_dumps_is_compact():
    assert dumps({"a": [1, 2]}) == '{"a":[1,2]}'


def test_envelope_fields(ctx):
    payload = Envelope(
        ctx, data=[1], total=3, returned=1, truncated=True, next_cursor="1", hint="h"
    ).build()
    assert payload["dataset"]["pdk"] == ctx.pdk
    assert payload["next_cursor"] == "1" and payload["hint"] == "h" and payload["truncated"] is True


def test_ok_within_budget(ctx):
    payload = ok(ctx, {"x": 1.123456789}, extra_key="v")
    assert payload["data"] == {"x": 1.12346}
    assert payload["extra_key"] == "v"
    assert payload["truncated"] is False


def test_ok_truncates_large_lists(tiny_ctx):
    payload = ok(tiny_ctx, {"rows": list(range(5000)), "small": [1, 2]})
    assert payload["truncated"] is True
    assert len(payload["data"]["rows"]) < 5000
    assert "hint" in payload
    assert len(dumps(payload)) <= tiny_ctx.max_response_chars


def test_ok_truncation_stops_when_nothing_to_cut(tiny_ctx):
    payload = ok(tiny_ctx, {"blob": "x" * 5000})
    assert payload["truncated"] is True  # cannot shrink a string; still flagged


def test_paged_no_truncation(ctx):
    rows = [{"i": i} for i in range(3)]
    payload = paged(ctx, rows, total=3)
    assert payload["returned"] == 3 and payload["total"] == 3
    assert payload["truncated"] is False and "next_cursor" not in payload


def test_paged_more_rows_available(ctx):
    payload = paged(ctx, [{"i": 0}], total=10, offset=4, hint="narrow it")
    assert payload["truncated"] is True
    assert payload["next_cursor"] == "5"
    assert payload["hint"] == "narrow it"


def test_paged_budget_cuts_rows(tiny_ctx):
    rows = [{"name": f"row-{i:04d}", "value": i * 1.5} for i in range(200)]
    payload = paged(tiny_ctx, rows, total=200, hint="use aggregates")
    assert len(dumps(payload)) <= tiny_ctx.max_response_chars
    assert 0 < payload["returned"] < 200
    assert payload["next_cursor"] == str(payload["returned"])
    assert payload["hint"].startswith("use aggregates")
    assert "response budget" in payload["hint"]


def test_paged_always_returns_one_row(tiny_ctx):
    rows = [{"blob": "x" * 5000}, {"blob": "y"}]
    payload = paged(tiny_ctx, rows, total=2)
    assert payload["returned"] == 1  # progress even if one row is over budget


def test_paged_wrap(ctx):
    payload = paged(ctx, [{"i": 1}], total=1, wrap=lambda r: {"rows": r})
    assert payload["data"] == {"rows": [{"i": 1}]}


@pytest.mark.parametrize("cursor, offset", [(None, 0), ("", 0), ("15", 15), ("-3", 0)])
def test_parse_cursor(cursor, offset):
    assert parse_cursor(cursor) == offset


def test_parse_cursor_invalid():
    with pytest.raises(McpInputError, match="Invalid cursor"):
        parse_cursor("abc")
