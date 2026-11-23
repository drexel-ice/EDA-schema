# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/__init__.py
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

"""Model Context Protocol (MCP) server for EDA-Schema datasets.

Install with ``pip install "eda-schema[mcp]"`` and run ``eda-schema-mcp
--dataset <root>``. One server process serves one per-PDK dataset.

:class:`DatasetContext` has no dependency on the ``mcp`` package; the server
itself is in :mod:`eda_schema.mcp.server`.
"""

from eda_schema.mcp.context import DatasetContext

__all__ = ["DatasetContext"]
