#!/usr/bin/env python3
"""
Example: Talk to the MCP Server Over stdio

Description: Starts `python -m eda_schema.mcp` as a subprocess, exactly as an
MCP client such as Claude Code would, and answers the phase 1 exit question:
"How does WNS evolve across stages, which path is worst at `final`, and show
me the routing map."

Prerequisites:
- pip install "eda-schema[mcp]"
- A per-PDK dataset root (default: dataset/test)

Key Concepts:
- stdio transport: the server reads MCP from stdin and writes to stdout
- Tool results carry JSON text plus structured content; render_image adds a PNG

Usage:
    python examples/08_mcp/02_stdio_client.py [dataset_path] [output_dir]

Output:
    Prints the answer and writes routing_final.png to output_dir
    (default: examples/08_mcp/output).
"""

import base64
import json
import sys
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters


async def main(dataset_path: str, output_dir: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "eda_schema.mcp", "--dataset", dataset_path, "--log-level", "ERROR"],
    )
    async with Client(params) as client:
        print("Server instructions:\n" + (client.instructions or "") + "\n")

        flows = await client.call_tool("list_flows", {"limit": 1})
        flow_id = json.loads(flows.content[0].text)["data"][0]["flow_id"]

        evo = await client.call_tool("get_stage_evolution", {"flow_id": flow_id, "metrics": ["worst_slack"]})
        stages = json.loads(evo.content[0].text)["data"]["stages"]
        print(f"WNS of {flow_id} by stage:")
        for row in stages:
            print(f"  {row['stage']:<15} {row['worst_slack']:>9.4f}")

        paths = await client.call_tool("list_timing_paths", {"flow_id": flow_id, "limit": 1})
        worst = json.loads(paths.content[0].text)["data"][0]
        print(f"\nWorst setup path at final: {worst['startpoint']} -> {worst['endpoint']} "
              f"(slack {worst['slack']})")

        detail = await client.call_tool("get_timing_path", {
            "flow_id": flow_id, "stage": "final",
            "startpoint": worst["startpoint"], "endpoint": worst["endpoint"],
        })
        totals = json.loads(detail.content[0].text)["data"]["totals"]
        print(f"  {totals['cell_arcs']} cell arcs, {totals['net_arcs']} net arcs")

        image = await client.call_tool("render_image", {
            "entity": "netlists", "name": "routing", "flow_id": flow_id, "stage": "final",
        })
        png = next(b for b in image.content if b.type == "image")
        info = json.loads(next(b.text for b in image.content if b.type == "text"))
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / "routing_final.png"
        out.write_bytes(base64.b64decode(png.data))
        print(f"\nRouting map {info['shape']} -> {info['output_px']} px written to {out}")


if __name__ == "__main__":
    dataset = sys.argv[1] if len(sys.argv) > 1 else "dataset/test"
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "output"
    anyio.run(main, dataset, output)
