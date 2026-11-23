# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/envelope.py
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

"""Response envelope, JSON cleaning and size budgeting.

Every tool returns the same envelope::

    {
      "dataset":   {"pdk": "...", "root_id": "..."},
      "data":      ...,
      "returned":  20,          # list tools only
      "total":     287,         # list tools only, when known
      "truncated": false,
      "next_cursor": "20",      # paginated tools only, when more rows exist
      "hint":      "..."        # optional advice on a cheaper follow-up
    }

Two limits keep responses small enough for a model's context window: a
row ``limit`` (clamped to ``DatasetContext.max_rows``) and a character budget
(``DatasetContext.max_response_chars``) applied to the serialized response.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

if TYPE_CHECKING:  # pragma: no cover
    from eda_schema.mcp.context import DatasetContext


def round_sig(value: float, digits: int) -> float:
    """Round ``value`` to ``digits`` significant digits."""
    if value == 0 or not math.isfinite(value):
        return value
    return round(value, digits - 1 - math.floor(math.log10(abs(value))))


def clean(value: Any, digits: int = 6) -> Any:
    """Convert ``value`` into plain JSON-safe Python.

    * numpy and pandas scalars become Python scalars;
    * ``NaN`` and missing values become ``None``;
    * ``inf`` / ``-inf`` become the strings ``"inf"`` / ``"-inf"``
      (pin slacks use ``inf`` for unconstrained transitions);
    * floats are rounded to ``digits`` significant digits.
    """
    if isinstance(value, dict):
        return {str(k): clean(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v, digits) for v in value]
    if isinstance(value, np.ndarray):
        return [clean(v, digits) for v in value.tolist()]
    if isinstance(value, np.generic):
        value = value.item()
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return round_sig(value, digits)
    if isinstance(value, (int, str)):
        return value
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return str(value)


def records(df: pd.DataFrame, columns: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """DataFrame -> list of row dicts (not yet cleaned)."""
    if columns is not None:
        df = df[[c for c in columns if c in df.columns]]
    out = df.to_dict(orient="records")
    for row in out:
        for key, val in row.items():
            if isinstance(val, pd.api.extensions.ExtensionArray):  # pragma: no cover
                row[key] = list(val)
    return out


def dumps(payload: Any) -> str:
    """Compact JSON used for the text content of every tool result."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


@dataclass
class Envelope:
    """Builder for one tool response."""

    ctx: DatasetContext
    data: Any = None
    total: int | None = None
    returned: int | None = None
    truncated: bool = False
    next_cursor: str | None = None
    hint: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def build(self) -> dict[str, Any]:
        """Return the cleaned envelope dict."""
        payload: dict[str, Any] = {"dataset": self.ctx.dataset_ref()}
        payload.update(self.extra)
        payload["data"] = self.data
        if self.returned is not None:
            payload["returned"] = self.returned
        if self.total is not None:
            payload["total"] = self.total
        payload["truncated"] = bool(self.truncated)
        if self.next_cursor is not None:
            payload["next_cursor"] = self.next_cursor
        if self.hint:
            payload["hint"] = self.hint
        return clean(payload, self.ctx.precision)


def ok(ctx: DatasetContext, data: Any, *, hint: str | None = None, **extra: Any) -> dict[str, Any]:
    """Envelope for a single-object response, trimmed to the budget if needed."""
    payload = Envelope(ctx, data=data, hint=hint, extra=extra).build()
    if len(dumps(payload)) > ctx.max_response_chars:
        payload["data"] = _truncate_obj(payload["data"], ctx.max_response_chars // 2)
        payload["truncated"] = True
        payload.setdefault(
            "hint", "Response exceeded the size budget; nested lists were shortened."
        )
    return payload


def _truncate_obj(obj: Any, budget: int) -> Any:
    """Shorten the longest lists inside ``obj`` until it fits ``budget`` chars."""
    while len(dumps(obj)) > budget:
        longest: list[Any] | None = None

        def visit(node: Any) -> None:
            nonlocal longest
            if isinstance(node, list):
                if longest is None or len(node) > len(longest):
                    longest = node
                for item in node:
                    visit(item)
            elif isinstance(node, dict):
                for item in node.values():
                    visit(item)

        visit(obj)
        if not longest or len(longest) <= 1:
            break
        del longest[len(longest) // 2 :]
    return obj


def paged(
    ctx: DatasetContext,
    rows: list[dict[str, Any]],
    *,
    total: int,
    offset: int = 0,
    hint: str | None = None,
    wrap: Callable[[list[dict[str, Any]]], Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Envelope for a list response.

    ``rows`` is the already-limited page. If the serialized response is over
    the character budget, rows are dropped from the end until it fits, and
    ``truncated`` / ``next_cursor`` are set so the caller can continue.

    Args:
        ctx: Dataset context (budget, precision, identity).
        rows: Page of rows (``limit`` already applied).
        total: Number of rows matching the query before paging.
        offset: Offset of the first row of ``rows`` within the full result.
        hint: Advice shown when the result is truncated.
        wrap: Optional function turning the row list into the ``data`` value.
        extra: Additional top-level keys (keyword arguments).
    """
    wrap = wrap or (lambda r: r)
    rows = clean(rows, ctx.precision)

    def build(page: list[dict[str, Any]], note: str | None = None) -> dict[str, Any]:
        end = offset + len(page)
        more = end < total
        text = " ".join(t for t in (hint if more else None, note) if t) or None
        env = Envelope(
            ctx,
            data=wrap(page),
            total=total,
            returned=len(page),
            truncated=more,
            next_cursor=str(end) if more else None,
            hint=text,
            extra=extra,
        )
        return env.build()

    payload = build(rows)
    if len(dumps(payload)) <= ctx.max_response_chars:
        return payload

    def note(n: int) -> str:
        return f"Page cut to {n} rows by the {ctx.max_response_chars}-character response budget."

    lo, hi = 0, len(rows)  # largest n such that build(rows[:n]) fits
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if len(dumps(build(rows[:mid], note(mid)))) <= ctx.max_response_chars:
            lo = mid
        else:
            hi = mid - 1
    lo = max(lo, 1)  # always make progress, even if one row is over budget
    return build(rows[:lo], note(lo))


def parse_cursor(cursor: str | None) -> int:
    """Cursor -> row offset. Cursors are opaque to callers but are offsets here."""
    if cursor in (None, ""):
        return 0
    try:
        offset = int(cursor)
    except (TypeError, ValueError):
        from eda_schema.mcp.errors import McpInputError

        raise McpInputError(f"Invalid cursor {cursor!r}; pass next_cursor from a previous call.")
    return max(0, offset)
