#!/usr/bin/env python3
"""
Example: Render Every Stored Image of One Stage

Description: Uses the tool functions directly (no MCP protocol) to list the
images of a flow at one stage and save each one as the PNG the server would
send to a model. Useful for checking what an agent will "see".

Prerequisites:
- pip install "eda-schema[mcp]"
- A per-PDK dataset root (default: dataset/test)

Key Concepts:
- Tool functions are plain Python: tool(ctx, **arguments)
- Binary maps are max-pooled, scalar heatmaps are colour-mapped

Usage:
    python examples/08_mcp/03_render_images.py [dataset_path] [stage] [output_dir]

Output:
    One PNG per image in output_dir (default: examples/08_mcp/output/<stage>).
"""

import sys
from pathlib import Path

from eda_schema.mcp import DatasetContext
from eda_schema.mcp.tools import catalog, images


def main(dataset_path: str, stage: str, output_dir: Path) -> None:
    ctx = DatasetContext(dataset_path)
    flow_id = catalog.list_flows(ctx, limit=1)["data"][0]["flow_id"]
    listing = images.list_images(ctx, flow_id, stage)["data"]["images"]
    output_dir.mkdir(parents=True, exist_ok=True)

    for entity, items in listing.items():
        for item in items:
            name = item if isinstance(item, str) else item["name"]
            clock = None if isinstance(item, str) else item.get("clock_source")
            result = images.render_image(ctx, entity, name, flow_id, stage, clock_source=clock)
            suffix = f"__{clock}" if clock else ""
            path = output_dir / f"{entity}__{name}{suffix}.png"
            path.write_bytes(result.png)
            info = result.info
            print(f"{path.name:<60} {info['kind']:<6} {info['shape']} -> {info['output_px']}")


if __name__ == "__main__":
    dataset = sys.argv[1] if len(sys.argv) > 1 else "dataset/test"
    stage = sys.argv[2] if len(sys.argv) > 2 else "final"
    output = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).parent / "output" / stage
    main(dataset, stage, output)
