#!/usr/bin/env python3
"""
Example: Query a Dataset Through the MCP Server (In-Process)

Description: Builds the EDA-Schema MCP server for one dataset and calls its
tools through the MCP client in the same process, without a subprocess. This
is the quickest way to see what an agent receives from each tool.

Prerequisites:
- pip install "eda-schema[mcp]"
- A per-PDK dataset root (default: dataset/test)

Key Concepts:
- DatasetContext: one session = one per-PDK dataset
- build_server: registers the tools and resources
- The response envelope: dataset, data, returned/total/truncated, next_cursor

Usage:
    python examples/08_mcp/01_inprocess_client.py [dataset_path]

Output:
    Prints dataset info, a QoR summary, the worst setup paths and the
    stage-by-stage evolution of worst slack.
"""

import json
import sys

import anyio
from mcp import Client

from eda_schema.mcp import DatasetContext
from eda_schema.mcp.server import build_server


def show(title: str, payload: dict) -> None:
    """Print a tool response, without the identity block."""
    print("=" * 60)
    print(title)
    print("=" * 60)
    body = {k: v for k, v in payload.items() if k != "dataset"}
    print(json.dumps(body, indent=2)[:2000])


async def main(dataset_path: str) -> None:
    server = build_server(DatasetContext(dataset_path))

    async with Client(server) as client:
        async def call(name: str, **args) -> dict:
            result = await client.call_tool(name, args)
            if result.is_error:
                raise RuntimeError(result.content[0].text)
            return result.structured_content

        info = await call("get_dataset_info")
        print(f"Serving PDK {info['data']['pdk']!r} ({info['data']['counts']['flows']} flows)\n")

        flows = await call("list_flows", limit=5)
        flow_id = flows["data"][0]["flow_id"]
        show(f"list_flows (first page, {flows['total']} total)", flows)

        show("get_qor (timing, final)", await call("get_qor", flow_id=flow_id, categories=["timing"]))

        paths = await call("list_timing_paths", flow_id=flow_id, limit=3)
        show("list_timing_paths (3 worst setup paths)", paths)

        evolution = await call("get_stage_evolution", flow_id=flow_id, metrics=["worst_slack"])
        print("=" * 60)
        print("worst_slack by stage")
        print("=" * 60)
        for row in evolution["data"]["stages"]:
            print(f"  {row['stage']:<15} {row['worst_slack']:>9.4f}")
        jump = evolution["data"]["largest_change"]["worst_slack"]
        print(f"  largest change: {jump['from_stage']} -> {jump['to_stage']} ({jump['delta']:+.4f})")


if __name__ == "__main__":
    anyio.run(main, sys.argv[1] if len(sys.argv) > 1 else "dataset/test")
