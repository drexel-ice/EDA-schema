# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/mcp/test_mcp_render.py
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

"""Image downsampling, statistics and PNG rendering."""

import io

import numpy as np
import pytest
from PIL import Image

from eda_schema.mcp import render


def _png_size(data: bytes):
    with Image.open(io.BytesIO(data)) as img:
        return img.size, img.mode


def test_is_binary():
    assert render.is_binary(np.array([[0, 1]], dtype=np.uint8))
    assert render.is_binary(np.array([[True, False]]))
    assert not render.is_binary(np.array([[0.0, 0.5]]))
    assert not render.is_binary(np.array([[0, 1, 2]], dtype=np.uint8))


def test_max_pool_keeps_single_pixel_wire():
    arr = np.zeros((1000, 1000), dtype=np.uint8)
    arr[500, :] = 1  # one-pixel horizontal wire
    small, factor = render.downsample(arr, 100)
    assert factor == 10 and small.shape == (100, 100)
    assert small[50].all()  # still visible after max-pooling


def test_mean_pool_scalar_and_padding():
    arr = np.arange(25, dtype=float).reshape(5, 5)
    small, factor = render.downsample(arr, 2)
    assert factor == 3 and small.shape == (2, 2)


def test_no_downsample_when_small():
    arr = np.ones((10, 10), dtype=np.uint8)
    small, factor = render.downsample(arr, 512)
    assert factor == 1 and small is arr


def test_stats_binary_and_scalar():
    b = render.stats(np.array([[0, 1], [1, 1]], dtype=np.uint8))
    assert b["kind"] == "binary" and b["occupancy"] == 0.75
    s = render.stats(np.array([[1.0, np.nan], [3.0, 5.0]]))
    assert s["kind"] == "scalar" and s["max"] == 5.0 and "p99" in s


def test_to_png_binary():
    arr = np.zeros((700, 300), dtype=np.uint8)
    arr[::7, ::7] = 1
    png, info = render.to_png(arr, max_px=128)
    (w, h), mode = _png_size(png)
    assert max(w, h) <= 128 and mode == "L"
    assert info["pooling"] == "max" and info["downsample_factor"] == 6
    assert info["output_px"] == [h, w]


def test_to_png_scalar_upscales_small_maps():
    arr = np.random.default_rng(0).random((14, 14))
    png, info = render.to_png(arr, max_px=512)
    (w, h), mode = _png_size(png)
    assert mode == "RGB" and w == h and 400 <= w <= 512
    assert info["colormap"] == "inferno" and info["pooling"] == "mean"


def test_to_png_constant_scalar():
    png, info = render.to_png(np.full((4, 4), 2.5), max_px=64)
    assert info["min"] == info["max"] == 2.5
    assert _png_size(png)[1] == "RGB"


def test_to_png_clamps_max_px():
    arr = np.zeros((4000, 10), dtype=np.uint8)
    _, info = render.to_png(arr, max_px=5000)
    assert max(info["output_px"]) <= render.MAX_PX


def test_to_png_rejects_bad_input():
    with pytest.raises(ValueError, match="2-D"):
        render.to_png(np.zeros((2, 2, 2)))
    with pytest.raises(ValueError, match="colormap"):
        render.to_png(np.random.default_rng(1).random((4, 4)), colormap="not-a-cmap")


def test_load_npz(tmp_path):
    path = tmp_path / "x.npz"
    np.savez_compressed(path, np.eye(3))
    assert render.load_npz(path).shape == (3, 3)
