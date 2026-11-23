# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/mcp/test_mcp_server.py
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

"""The MCP protocol layer: tool listing, calls, errors, resources, budget, CLI.

Uses the SDK's in-process client, so no subprocess or network is involved.
"""

import base64
import io
import json

import anyio
import pytest
from mcp import Client
from PIL import Image

from eda_schema.mcp import server as srv
from eda_schema.mcp.envelope import dumps

from .conftest import FLOW, SAMPLE

PHASE1_TOOLS = [
    "get_dataset_info",
    "list_designs",
    "list_flows",
    "get_flow",
    "get_qor",
    "get_stage_evolution",
    "compare_flows",
    "aggregate_metrics",
    "get_timing_summary",
    "list_timing_paths",
    "get_timing_path",
    "get_netlist_summary",
    "list_images",
    "render_image",
]

#: Minimal arguments for every tool (defaults for everything else).
DEFAULT_CALLS = {
    "get_dataset_info": {},
    "list_designs": {},
    "list_flows": {},
    "get_flow": {"flow_id": FLOW},
    "get_qor": {"flow_id": FLOW},
    "get_stage_evolution": {"flow_id": FLOW},
    "compare_flows": {"flow_ids": [FLOW]},
    "aggregate_metrics": {"metric": "worst_slack"},
    "get_timing_summary": {"flow_id": FLOW},
    "list_timing_paths": {"flow_id": FLOW},
    "get_timing_path": {
        "flow_id": FLOW,
        "stage": "final",
        "startpoint": "_381_/Q",
        "endpoint": "_395_/D",
    },
    "get_netlist_summary": {"flow_id": FLOW},
    "list_images": {"flow_id": FLOW},
    "render_image": {"entity": "netlists", "name": "routing", "flow_id": FLOW},
}


def run(server, fn):
    """Run ``fn(client)`` against ``server`` over the in-process transport."""

    async def main():
        async with Client(server) as client:
            return await fn(client)

    return anyio.run(main)


@pytest.fixture(scope="module")
def server(ctx):
    return srv.build_server(ctx)


def test_instructions_name_the_pdk(ctx, server):
    text = run(server, lambda c: _instructions(c))
    assert "sky130hd" in text and "cross-PDK" in text
    assert srv.instructions_for(ctx) == text


async def _instructions(client):
    return client.instructions


def test_lists_phase1_tools(server):
    async def list_tools(c):
        return (await c.list_tools()).tools

    tools = run(server, list_tools)
    assert [t.name for t in tools] == PHASE1_TOOLS
    assert set(DEFAULT_CALLS) == set(PHASE1_TOOLS)
    for tool in tools:
        assert tool.description
        assert tool.annotations.read_only_hint is True
        props = tool.input_schema.get("properties", {})
        assert "ctx" not in props
        assert "pdk" not in props  # sessions are per-PDK; no tool takes a pdk


def test_input_schema_has_descriptions_and_bounds(server):
    async def schema(c):
        tools = {t.name: t for t in (await c.list_tools()).tools}
        return tools["list_flows"].input_schema, tools["render_image"].input_schema

    flows, render = run(server, schema)
    assert flows["properties"]["limit"]["minimum"] == 1
    assert "Range" in json.dumps(flows)
    assert render["properties"]["max_px"]["maximum"] == 1024
    assert set(render["required"]) == {"entity", "name", "flow_id"}


@pytest.mark.parametrize("name", PHASE1_TOOLS)
def test_every_tool_round_trips_within_budget(server, ctx, name):
    async def call(c):
        return await c.call_tool(name, DEFAULT_CALLS[name])

    result = run(server, call)
    assert not result.is_error, result.content
    text = next(b.text for b in result.content if b.type == "text")
    payload = json.loads(text)
    assert payload["dataset"] == ctx.dataset_ref()
    assert result.structured_content == payload
    assert len(text) <= ctx.max_response_chars


def test_render_image_returns_png(server):
    async def call(c):
        return await c.call_tool(
            "render_image",
            {"entity": "netlists", "name": "routing", "flow_id": FLOW, "max_px": 128},
        )

    result = run(server, call)
    image = result.content[0]
    assert image.type == "image" and image.mime_type == "image/png"
    with Image.open(io.BytesIO(base64.b64decode(image.data))) as img:
        assert max(img.size) <= 128


@pytest.mark.parametrize(
    "name, args, needle",
    [
        ("get_flow", {"flow_id": "gcd-1"}, "Closest matches: gcd-000001"),
        ("get_qor", {"flow_id": FLOW, "stage": "cst"}, "Closest matches: cts"),
        ("aggregate_metrics", {"metric": "nope"}, "Unknown metric"),
        ("list_flows", {"cursor": "abc"}, "Invalid cursor"),
    ],
)
def test_input_errors_are_readable_tool_errors(server, name, args, needle):
    async def call(c):
        return await c.call_tool(name, args)

    result = run(server, call)
    assert result.is_error
    assert needle in result.content[0].text


def test_schema_validation_errors(server):
    async def call(c):
        return await c.call_tool("list_flows", {"limit": 0})

    assert run(server, call).is_error


def test_tiny_budget_truncates_over_protocol(tiny_ctx):
    server = srv.build_server(tiny_ctx)

    async def call(c):
        return await c.call_tool("list_timing_paths", {"flow_id": FLOW, "limit": 200})

    payload = json.loads(run(server, call).content[0].text)
    assert payload["truncated"] is True and payload["returned"] <= 5
    assert payload["total"] == 137 and "next_cursor" in payload
    assert len(dumps(payload)) <= tiny_ctx.max_response_chars


# ----------------------------------------------------------------------
# Resources
# ----------------------------------------------------------------------
def _leaf_messages(exc: BaseException):
    """Messages of all leaf exceptions (the client wraps MCPError in groups)."""
    subs = getattr(exc, "exceptions", None)
    if not subs:
        return [str(exc)]
    return [m for sub in subs for m in _leaf_messages(sub)]


def _read_error(server, uri) -> str:
    with pytest.raises(BaseException) as info:
        _read(server, uri)
    return " ".join(_leaf_messages(info.value))


def _read(server, uri):
    async def read(c):
        return (await c.read_resource(uri)).contents[0]

    return run(server, read)


def test_resource_listing(server):
    async def listing(c):
        static = [str(r.uri) for r in (await c.list_resources()).resources]
        templates = [t.uri_template for t in (await c.list_resource_templates()).resource_templates]
        return static, templates

    static, templates = run(server, listing)
    assert set(static) == {"eda://dataset", "eda://dataset/summary", "eda://schema", "eda://stages"}
    assert set(templates) == {
        "eda://schema/{entity}",
        "eda://flows/{flow_id}",
        "eda://flows/{flow_id}/{stage}/qor",
        "eda://image/{entity}/{name}/{flow_id}/{stage}",
    }


def test_dataset_resources(server):
    info = json.loads(_read(server, "eda://dataset").text)
    assert info["pdk"] == "sky130hd" and info["counts"]["flows"] == 1
    summary = json.loads(_read(server, "eda://dataset/summary").text)
    assert summary["designs"][0]["design"] == "gcd"


def test_schema_resources(server):
    schema = json.loads(_read(server, "eda://schema").text)["entities"]
    assert schema["timing_paths"]["primary_key"] == [
        "flow_id",
        "stage",
        "startpoint",
        "endpoint",
        "path_type",
    ]
    assert schema["netlists"]["graph"] is True
    assert "routing" in schema["netlists"]["images"]
    assert "GATE" in schema["netlists"]["graph_node_types"]
    gates = json.loads(_read(server, "eda://schema/gates").text)
    assert "total_power" in gates["defined_but_absent"]
    assert gates["description"] == "Placed gate instance."
    assert any(c["name"] == "standard_cell" for c in gates["columns"])


def test_schema_resource_unknown_entity(server):
    assert "Unknown entity 'nope'" in _read_error(server, "eda://schema/nope")


def test_stage_and_flow_resources(server):
    stages = json.loads(_read(server, "eda://stages").text)["stages"]
    assert stages[0]["stage"] == "floorplan"
    assert "netlists/routing" in stages[-1]["image_kinds"]
    flow = json.loads(_read(server, f"eda://flows/{FLOW}").text)
    assert flow["design"] == "gcd"
    q = json.loads(_read(server, f"eda://flows/{FLOW}/cts/qor").text)
    assert q["stage"] == "cts" and "timing" in q["metrics"]


def test_flow_resource_unknown(server):
    assert "Unknown flow_id 'nope'" in _read_error(server, "eda://flows/nope")
    assert "Closest matches: cts" in _read_error(server, f"eda://flows/{FLOW}/cst/qor")


def test_image_resource(server):
    blob = _read(server, f"eda://image/routability_metrics/rudy_net/{FLOW}/final")
    assert blob.mime_type == "image/png"
    with Image.open(io.BytesIO(base64.b64decode(blob.blob))) as img:
        assert img.format == "PNG"


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def test_parse_args_env(monkeypatch):
    monkeypatch.setenv(srv.ENV_DATASET, str(SAMPLE))
    args = srv.parse_args([])
    assert args.dataset == str(SAMPLE) and args.max_rows == 200


def test_parse_args_requires_dataset(monkeypatch):
    monkeypatch.delenv(srv.ENV_DATASET, raising=False)
    with pytest.raises(SystemExit):
        srv.parse_args([])


def test_main_bad_root(tmp_path, capsys):
    assert srv.main(["--dataset", str(tmp_path)]) == 2
    assert "not an EDA-Schema dataset" in capsys.readouterr().err


def test_main_runs_stdio(monkeypatch):
    called = {}
    monkeypatch.setattr(
        srv.MCPServer,
        "run",
        lambda self, transport="stdio", **kw: called.setdefault("t", transport),
    )
    assert srv.main(["--dataset", str(SAMPLE), "--max-rows", "10", "--log-level", "ERROR"]) == 0
    assert called["t"] == "stdio"


def test_python_dash_m_entry(monkeypatch):
    import runpy

    monkeypatch.setattr(srv, "main", lambda: 0)
    with pytest.raises(SystemExit) as info:
        runpy.run_module("eda_schema.mcp", run_name="__main__")
    assert info.value.code == 0


def test_stdio_subprocess_end_to_end():
    """Launch the real server as a subprocess and talk to it over stdio."""
    import sys

    from mcp import StdioServerParameters

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "eda_schema.mcp", "--dataset", str(SAMPLE), "--log-level", "ERROR"],
    )

    async def main():
        async with Client(params) as client:
            tools = [t.name for t in (await client.list_tools()).tools]
            result = await client.call_tool("get_qor", {"flow_id": FLOW, "categories": ["timing"]})
            return tools, json.loads(result.content[0].text)

    tools, payload = anyio.run(main)
    assert tools == PHASE1_TOOLS
    assert payload["data"]["metrics"]["timing"]["worst_slack"] == -0.2732
