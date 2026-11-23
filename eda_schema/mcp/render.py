# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/render.py
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

"""Turn stored ``.npz`` layout images into small PNGs and statistics.

Two kinds of image are stored:

* **binary maps** (placement, routing, PDN routing, pins): ``uint8`` 0/1 at one
  pixel per minimum M1 width, so they can be thousands of pixels per side.
  They are shrunk with **max-pooling**, so a one-pixel wire stays visible.
* **scalar maps** (IR drop, EM, RUDY): ``float`` at 50x coarser resolution.
  They are colour-mapped; small maps are enlarged with nearest-neighbour
  scaling and large maps are shrunk with **mean-pooling**.

Orientation follows :meth:`eda_schema.base.Image2D.plot` (row 0 at the top).
"""

from __future__ import annotations

import io
import math
from typing import Any

import numpy as np
from PIL import Image as PILImage

MIN_PX = 32
MAX_PX = 1024


def load_npz(path) -> np.ndarray:
    """Load the ``arr_0`` array of an image file."""
    with np.load(path) as data:
        return np.asarray(data["arr_0"])


def is_binary(arr: np.ndarray) -> bool:
    """True for 0/1 (or two-valued integer) layout masks."""
    if arr.dtype == bool:
        return True
    if not np.issubdtype(arr.dtype, np.integer):
        return False
    return np.unique(arr).size <= 2


def _pool(arr: np.ndarray, factor: int, reducer) -> np.ndarray:
    """Block-reduce ``arr`` by an integer ``factor`` on both axes (pads the edge)."""
    if factor <= 1:
        return arr
    h, w = arr.shape
    ph, pw = (-h) % factor, (-w) % factor
    if ph or pw:
        arr = np.pad(arr, ((0, ph), (0, pw)), mode="edge")
    h2, w2 = arr.shape[0] // factor, arr.shape[1] // factor
    blocks = arr.reshape(h2, factor, w2, factor)
    return reducer(blocks, axis=(1, 3))


def downsample(arr: np.ndarray, max_px: int) -> tuple[np.ndarray, int]:
    """Shrink ``arr`` so neither side exceeds ``max_px``. Returns (array, factor)."""
    factor = max(1, math.ceil(max(arr.shape) / max_px))
    reducer = np.max if is_binary(arr) else np.mean
    return _pool(arr, factor, reducer), factor


def stats(arr: np.ndarray) -> dict[str, Any]:
    """Cheap summary statistics of an image."""
    finite = arr[np.isfinite(arr)] if np.issubdtype(arr.dtype, np.floating) else arr
    out: dict[str, Any] = {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "kind": "binary" if is_binary(arr) else "scalar",
    }
    if finite.size:
        out.update(min=float(finite.min()), max=float(finite.max()), mean=float(finite.mean()))
    if out["kind"] == "binary":
        out["occupancy"] = float(np.count_nonzero(arr) / arr.size)
    elif finite.size:
        out["p50"] = float(np.percentile(finite, 50))
        out["p99"] = float(np.percentile(finite, 99))
    return out


def to_png(
    arr: np.ndarray, max_px: int = 512, colormap: str = "inferno"
) -> tuple[bytes, dict[str, Any]]:
    """Render ``arr`` to PNG bytes no larger than ``max_px`` on either side.

    Args:
        arr: 2-D image array.
        max_px: Longest output side, clamped to ``[32, 1024]``.
        colormap: Matplotlib colormap name used for scalar maps.

    Returns:
        ``(png_bytes, info)`` where ``info`` describes the source and output.
    """
    if arr.ndim != 2:
        raise ValueError(f"Expected a 2-D image, got shape {arr.shape}")
    max_px = max(MIN_PX, min(int(max_px), MAX_PX))
    info = stats(arr)
    small, factor = downsample(arr, max_px)

    if info["kind"] == "binary":
        img = PILImage.fromarray(np.where(small > 0, 255, 0).astype(np.uint8))
    else:
        import matplotlib

        try:
            cmap = matplotlib.colormaps[colormap]
        except KeyError:
            raise ValueError(f"Unknown colormap {colormap!r}") from None
        data = np.nan_to_num(small.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
        lo, hi = float(data.min()), float(data.max())
        norm = (data - lo) / (hi - lo) if hi > lo else np.zeros_like(data)
        rgb = (cmap(norm)[:, :, :3] * 255).astype(np.uint8)
        img = PILImage.fromarray(rgb)
        scale = max(1, max_px // max(small.shape))
        if scale > 1:  # enlarge tiny heatmaps so they are legible
            img = img.resize((img.width * scale, img.height * scale), PILImage.NEAREST)
        info["colormap"] = colormap

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    info.update(
        downsample_factor=factor,
        output_px=[img.height, img.width],
        pooling="max" if info["kind"] == "binary" else "mean",
    )
    return buf.getvalue(), info
