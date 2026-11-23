# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/errors.py
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

"""Errors raised by the MCP layer.

Every error a tool raises on purpose is a :class:`McpInputError`. The server
turns it into an MCP tool error (``is_error=True``) whose text the model can
read and act on, so messages always say what was wrong and list valid values.
"""

from __future__ import annotations

import difflib
from collections.abc import Iterable, Sequence


class DatasetRootError(RuntimeError):
    """The dataset root is missing or is not an EDA-Schema Parquet dataset."""


class McpInputError(ValueError):
    """A tool argument does not match anything in the dataset."""

    def __init__(self, message: str, valid: Sequence[str] | None = None):
        self.valid = list(valid) if valid else []
        if self.valid:
            message = f"{message} Valid values: {', '.join(map(str, self.valid))}."
        super().__init__(message)


def not_found(kind: str, value: object, candidates: Iterable[str], show: int = 10) -> McpInputError:
    """Build an error for an unknown value, suggesting close matches first.

    Args:
        kind: What was looked up, e.g. ``"flow_id"``.
        value: The value the caller passed.
        candidates: All valid values.
        show: Maximum number of values to list.
    """
    candidates = [str(c) for c in candidates]
    close = difflib.get_close_matches(str(value), candidates, n=show, cutoff=0.5)
    listed = close or candidates[:show]
    more = len(candidates) - len(listed)
    suffix = f" (+{more} more)" if more > 0 and not close else ""
    label = "Closest matches" if close else "Valid values"
    message = f"Unknown {kind} {value!r}."
    if listed:
        message += f" {label}: {', '.join(listed)}{suffix}."
    return McpInputError(message)
