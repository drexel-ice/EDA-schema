# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/tools/images.py
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

"""Image tools (mcp_plan.md section 6.8, phase 1 subset).

Raw arrays are never returned: images are served as downsampled PNGs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from pydantic import Field

from eda_schema.mcp import render
from eda_schema.mcp.context import DatasetContext, ImageRef
from eda_schema.mcp.envelope import clean, ok
from eda_schema.mcp.errors import McpInputError, not_found
from eda_schema.mcp.tools.qor import FlowId, Stage


@dataclass
class ImageResult:
    """A rendered PNG plus a JSON-able description, returned by render_image."""

    png: bytes
    info: dict[str, Any]


def list_images(ctx: DatasetContext, flow_id: FlowId, stage: Stage = "final") -> dict[str, Any]:
    """List the images stored for one flow at one stage, grouped by entity.

    Pass an (entity, name) pair to render_image. Clock-tree images also need
    their clock_source.
    """
    ctx.require_flow(flow_id)
    ctx.require_stage(flow_id, stage)
    grouped: dict[str, list[Any]] = {}
    for ref in ctx.images_for(flow_id, stage):
        item: Any = ref.name if not ref.extra else {"name": ref.name, **ref.extra}
        grouped.setdefault(ref.entity, []).append(item)
    return ok(ctx, {"flow_id": flow_id, "stage": stage, "images": grouped})


def find_image(
    ctx: DatasetContext,
    entity: str,
    name: str,
    flow_id: str,
    stage: str,
    clock_source: str | None = None,
) -> ImageRef:
    """Resolve an image reference or raise an error listing what exists."""
    ctx.require_flow(flow_id)
    ctx.require_stage(flow_id, stage)
    refs = ctx.images_for(flow_id, stage)
    entities = sorted({r.entity for r in refs})
    if entity not in entities:
        raise not_found("image entity", entity, entities)
    names = sorted({r.name for r in refs if r.entity == entity})
    matches = [r for r in refs if r.entity == entity and r.name == name]
    if not matches:
        raise not_found(f"{entity} image", name, names)
    if clock_source is not None:
        matches = [r for r in matches if r.clock_source == clock_source]
        if not matches:
            clocks = sorted(
                {r.clock_source or "" for r in refs if r.entity == entity and r.name == name}
            )
            raise not_found("clock_source", clock_source, clocks)
    if len(matches) > 1:
        options = sorted(r.clock_source or "" for r in matches)
        raise McpInputError(
            f"Image {entity}/{name} exists for several clock sources; pass clock_source.", options
        )
    return matches[0]


def render_image(
    ctx: DatasetContext,
    entity: Annotated[str, Field(description="Entity owning the image, e.g. 'netlists'.")],
    name: Annotated[str, Field(description="Image name from list_images, e.g. 'routing'.")],
    flow_id: FlowId,
    stage: Stage = "final",
    clock_source: Annotated[
        str | None, Field(description="Clock source, for clock_trees images only.")
    ] = None,
    max_px: Annotated[int, Field(ge=32, le=1024, description="Longest side of the PNG.")] = 512,
    colormap: Annotated[str, Field(description="Matplotlib colormap for scalar maps.")] = "inferno",
) -> ImageResult:
    """Render a stored layout image or heatmap as a PNG.

    Binary maps (placement, routing, pins, PDN) are shrunk with max-pooling so
    thin features stay visible; scalar maps (IR drop, EM, RUDY) are colour-mapped.
    Also returns the source shape, downsampling factor and value statistics.
    """
    ref = find_image(ctx, entity, name, flow_id, stage, clock_source)
    arr = render.load_npz(ref.path)
    try:
        png, info = render.to_png(arr, max_px=max_px, colormap=colormap)
    except ValueError as exc:
        raise McpInputError(str(exc)) from exc
    info = {
        "dataset": ctx.dataset_ref(),
        "entity": ref.entity,
        "name": ref.name,
        "flow_id": flow_id,
        "stage": stage,
        **({"clock_source": ref.clock_source} if ref.clock_source else {}),
        **info,
    }
    return ImageResult(png=png, info=clean(info, ctx.precision))
