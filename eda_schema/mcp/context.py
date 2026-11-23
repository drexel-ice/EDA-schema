# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/mcp/context.py
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

"""Per-session dataset state for the MCP server.

A :class:`DatasetContext` is bound to exactly one EDA-Schema dataset root,
which holds the flows of a single PDK. It is built once at startup and is
read-only afterwards, so it can be shared safely between worker threads.

At construction it loads only small data:

* the **flow catalog**: ``design_flows`` joined with ``constraints``;
* the **QoR catalog**: ``design_stages`` joined with every ``*_metrics`` table
  and the ``netlists`` table, one row per ``(flow_id, stage)``;
* the **image index**: parsed ``images/*.npz`` filenames;
* the Parquet **schemas and row counts** of every entity (metadata only).

Element tables (gates, pins, nets, arcs, timing paths) are never loaded
whole; tools read them through :class:`~eda_schema.db.ParquetDB` filtered by
``flow_id`` and ``stage``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

from eda_schema.db import ParquetDB
from eda_schema.entity import DesignStages, SchemaMetadata
from eda_schema.mcp.errors import DatasetRootError, McpInputError, not_found

logger = logging.getLogger(__name__)

STAGES: list[str] = DesignStages.tolist()
"""Design stages in flow order."""

ENTITY_NAMES: list[str] = [pair[0] for pair in SchemaMetadata.items()]
"""All entity (table) names defined by the schema."""

KEY_COLUMNS = ("flow_id", "stage")

QOR_TABLES: dict[str, str] = {
    "area": "area_metrics",
    "cell": "cell_metrics",
    "power": "power_metrics",
    "timing": "timing_metrics",
    "netlist": "netlists",
}
"""QoR category -> entity table holding one row per (flow_id, stage)."""

MANIFEST_NAME = "dataset.json"
LOG_NAME = "openroad_dataloader.log"

# Standard-cell name prefix -> OpenROAD-flow-scripts platform name.
_CELL_PREFIX_PDK: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^sky130_fd_sc_hd__"), "sky130hd"),
    (re.compile(r"^sky130_fd_sc_hs__"), "sky130hs"),
    (re.compile(r"^sg13g2_"), "ihp-sg13g2"),
    (re.compile(r"^(asap7sc7p5t|[A-Z0-9]+x[pP]?\d+_ASAP7)"), "asap7"),
    (re.compile(r"^[A-Z0-9]+_X\d+$"), "nangate45"),
]
_LOG_PLATFORM = re.compile(r"/platforms/([A-Za-z0-9_.\-]+)/")


@dataclass(frozen=True)
class ImageRef:
    """One stored image (``.npz``) and the keys parsed from its filename."""

    entity: str
    name: str
    flow_id: str
    stage: str
    path: Path
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def clock_source(self) -> str | None:
        """Clock source for clock-tree images, else ``None``."""
        return self.extra.get("clock_source")


def parse_image_filename(entity: str, path: Path) -> ImageRef | None:
    """Parse ``{name}__flow_id=X__stage=Y[__k=v...].npz`` into an :class:`ImageRef`.

    The image name itself may contain ``__`` (e.g. ``routing_by_metal__met1``);
    every part before the first ``key=value`` part belongs to the name.
    """
    if path.suffix != ".npz":
        return None
    parts = path.stem.split("__")
    name_parts: list[str] = []
    keys: dict[str, str] = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            keys[k] = v
        elif keys:
            return None  # name fragment after keys: not our format
        else:
            name_parts.append(part)
    if not name_parts or "flow_id" not in keys or "stage" not in keys:
        return None
    flow_id = keys.pop("flow_id")
    stage = keys.pop("stage")
    return ImageRef(entity, "__".join(name_parts), flow_id, stage, path, keys)


class DatasetContext:
    """Read-only view of one per-PDK EDA-Schema dataset.

    Args:
        root: Dataset root directory (same layout as ``dataset/test``).
        max_rows: Hard maximum for any tool's ``limit`` argument.
        max_response_chars: Character budget for one serialized tool response.
        precision: Significant digits used when rounding floats in responses.

    Raises:
        DatasetRootError: If ``root`` is not an EDA-Schema Parquet dataset.
    """

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        max_rows: int = 200,
        max_response_chars: int = 40_000,
        precision: int = 6,
    ):
        self.root = Path(root).expanduser().resolve()
        flows_table = self.root / "design_flows" / "table.parquet"
        if not flows_table.exists():
            raise DatasetRootError(
                f"{self.root} is not an EDA-Schema dataset: missing design_flows/table.parquet"
            )

        self.max_rows = max_rows
        self.max_response_chars = max_response_chars
        self.precision = precision

        self.db = ParquetDB(self.root)
        self.manifest: dict[str, Any] = self._load_manifest()
        self.pdk, self.pdk_source = self._detect_pdk()
        digest = hashlib.sha1(str(self.root).encode()).hexdigest()[:8]
        self.root_id = f"{self.pdk}@{digest}"

        self.entity_columns, self.entity_rows = self._read_entity_metadata()
        self.flows = self._load_flows()
        self.qor, self.metric_category = self._load_qor()
        self.images = self._index_images()

        logger.info(
            "Loaded dataset %s (pdk=%s via %s): %d flows, %d stage rows, %d images",
            self.root,
            self.pdk,
            self.pdk_source,
            len(self.flows),
            len(self.qor),
            sum(len(v) for v in self.images.values()),
        )

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def _load_manifest(self) -> dict[str, Any]:
        path = self.root / MANIFEST_NAME
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("Ignoring unreadable %s: %s", path, exc)
            return {}
        return data if isinstance(data, dict) else {}

    def _detect_pdk(self) -> tuple[str, str]:
        """Return ``(pdk, source)``; see mcp_plan.md section 2 for the order."""
        pdk = self.manifest.get("pdk")
        if isinstance(pdk, str) and pdk:
            return pdk, "manifest"

        log = self.root / LOG_NAME
        if log.exists():
            try:
                with log.open(encoding="utf-8", errors="replace") as fh:
                    for _, line in zip(range(200), fh):
                        match = _LOG_PLATFORM.search(line)
                        if match:
                            return match.group(1), "dataloader_log"
            except OSError as exc:
                logger.warning("Could not read %s: %s", log, exc)

        cells = self.root / "standard_cells" / "table.parquet"
        if cells.exists():
            names = pq.read_table(cells, columns=["name"]).column("name").to_pylist()
            for pattern, name in _CELL_PREFIX_PDK:
                hits = sum(1 for n in names[:200] if n and pattern.search(n))
                if names and hits >= max(1, len(names[:200]) // 2):
                    return name, "standard_cell_names"

        logger.warning("Could not determine the PDK of %s", self.root)
        return "unknown", "unknown"

    def _read_entity_metadata(self) -> tuple[dict[str, list[str]], dict[str, int]]:
        columns: dict[str, list[str]] = {}
        rows: dict[str, int] = {}
        for entity_name in ENTITY_NAMES:
            path = self.root / entity_name / "table.parquet"
            if not path.exists():
                continue
            pf = pq.ParquetFile(path)
            columns[entity_name] = [c for c in pf.schema_arrow.names if not c.startswith("_")]
            rows[entity_name] = pf.metadata.num_rows
        return columns, rows

    def _table(self, entity_name: str) -> pd.DataFrame:
        if entity_name not in self.entity_columns:
            return pd.DataFrame()
        return self.db.get_table_data(entity_name)

    def _load_flows(self) -> pd.DataFrame:
        flows = self._table("design_flows")
        constraints = self._table("constraints")
        if not constraints.empty:
            flows = flows.merge(constraints, on="flow_id", how="left")
        return flows.sort_values("flow_id").reset_index(drop=True)

    def _load_qor(self) -> tuple[pd.DataFrame, dict[str, str]]:
        stages = self._table("design_stages").rename(columns={"run_status": "stage_status"})
        category: dict[str, str] = {}
        qor = stages
        for cat, entity_name in QOR_TABLES.items():
            table = self._table(entity_name)
            if table.empty:
                continue
            table = table[[c for c in table.columns if not c.startswith("_")]]
            value_cols = [c for c in table.columns if c not in KEY_COLUMNS]
            for col in value_cols:
                category[col] = cat
            qor = qor.merge(table, on=list(KEY_COLUMNS), how="outer")
        if "stage" in qor:
            qor["stage"] = pd.Categorical(qor["stage"], categories=STAGES, ordered=True)
            qor = qor.sort_values(["flow_id", "stage"]).reset_index(drop=True)
        return qor, category

    def _index_images(self) -> dict[tuple[str, str], list[ImageRef]]:
        index: dict[tuple[str, str], list[ImageRef]] = {}
        for entity_name in ENTITY_NAMES:
            image_dir = self.root / entity_name / "images"
            if not image_dir.is_dir():
                continue
            with os.scandir(image_dir) as it:
                for entry in it:
                    ref = parse_image_filename(entity_name, Path(entry.path))
                    if ref is not None:
                        index.setdefault((ref.flow_id, ref.stage), []).append(ref)
        for refs in index.values():
            refs.sort(key=lambda r: (r.entity, r.name, sorted(r.extra.items())))
        return index

    # ------------------------------------------------------------------
    # Lookups used by tools
    # ------------------------------------------------------------------
    @property
    def version(self) -> str:
        """Installed ``eda-schema`` package version."""
        try:
            return metadata.version("eda-schema")
        except metadata.PackageNotFoundError:  # pragma: no cover - source checkout
            return "unknown"

    @property
    def designs(self) -> list[str]:
        """Sorted design names present in the dataset."""
        return sorted(self.flows["design"].dropna().unique().tolist())

    @property
    def flow_ids(self) -> list[str]:
        """Sorted flow ids present in the dataset."""
        return self.flows["flow_id"].tolist()

    @property
    def constraint_columns(self) -> list[str]:
        """Constraint columns present in the flow catalog."""
        return [c for c in self.entity_columns.get("constraints", []) if c != "flow_id"]

    @property
    def metric_columns(self) -> list[str]:
        """Numeric QoR columns available in the QoR catalog."""
        return [
            c
            for c in self.metric_category
            if c in self.qor.columns and pd.api.types.is_numeric_dtype(self.qor[c])
        ]

    def dataset_ref(self) -> dict[str, str]:
        """Identity block carried by every tool response."""
        return {"pdk": self.pdk, "root_id": self.root_id}

    def require_flow(self, flow_id: str) -> dict[str, Any]:
        """Return the catalog row of ``flow_id`` or raise a helpful error."""
        match = self.flows[self.flows["flow_id"] == flow_id]
        if match.empty:
            raise not_found("flow_id", flow_id, self.flow_ids)
        return match.iloc[0].to_dict()

    def require_design(self, design: str) -> str:
        """Validate a design name."""
        if design not in self.designs:
            raise not_found("design", design, self.designs)
        return design

    def stages_of(self, flow_id: str) -> list[str]:
        """Stages that have a QoR row for ``flow_id``, in flow order."""
        rows = self.qor[self.qor["flow_id"] == flow_id]
        return [str(s) for s in rows["stage"].dropna().tolist()]

    def require_stage(self, flow_id: str, stage: str) -> str:
        """Validate ``stage`` in general and for ``flow_id`` in particular."""
        if stage not in STAGES:
            raise not_found("stage", stage, STAGES)
        available = self.stages_of(flow_id)
        if stage not in available:
            raise McpInputError(
                f"Stage {stage!r} is not available for flow {flow_id!r}.", available
            )
        return stage

    def require_metrics(self, metrics: list[str]) -> list[str]:
        """Validate QoR metric names."""
        valid = self.metric_columns
        for name in metrics:
            if name not in valid:
                raise not_found("metric", name, valid, show=15)
        return metrics

    def qor_row(self, flow_id: str, stage: str) -> dict[str, Any]:
        """QoR catalog row for one (flow_id, stage)."""
        rows = self.qor[(self.qor["flow_id"] == flow_id) & (self.qor["stage"] == stage)]
        if rows.empty:  # pragma: no cover - guarded by require_stage
            raise McpInputError(f"No QoR row for {flow_id!r} at {stage!r}.")
        row = rows.iloc[0].to_dict()
        row["stage"] = str(row["stage"])
        return row

    def images_for(self, flow_id: str, stage: str) -> list[ImageRef]:
        """All indexed images for one (flow_id, stage)."""
        return list(self.images.get((flow_id, stage), []))

    def image_kinds(self) -> dict[str, list[str]]:
        """Distinct image names per entity across the whole dataset."""
        kinds: dict[str, set[str]] = {}
        for refs in self.images.values():
            for ref in refs:
                kinds.setdefault(ref.entity, set()).add(ref.name)
        return {k: sorted(v) for k, v in sorted(kinds.items())}

    def clamp_limit(self, limit: int) -> int:
        """Clamp a requested row limit to ``[1, max_rows]``."""
        return max(1, min(int(limit), self.max_rows))
