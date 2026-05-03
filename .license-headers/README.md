# Drexel ICE License Headers

Canonical source-file header templates for **EDA-Schema**.
Maintained by the Drexel University Integrated Circuits and Electronics (ICE)
Laboratory and licensed under
[CC BY-NC-SA 4.0](../LICENCE).

> **Status:** Templates approved. Application across the existing codebase is
> tracked as a single bulk update in [`../CHANGELOG.md`](../CHANGELOG.md)
> under the `[Unreleased]` → `Changed` section. **New** files must include
> the header on creation.

This directory is the single source of truth for the header text. Do not
duplicate the wording elsewhere; reference these files instead. The narrative
specification (rules, field semantics) lives in
[`../CONTRIBUTING.md`](../CONTRIBUTING.md#standardized-file-header-drexel-ice).

---

## Files

| Template | Applies to | Comment style |
|---|---|---|
| [`python.txt`](python.txt) | `*.py` | `#` |
| [`shell.txt`](shell.txt)   | `*.sh`, `*.bash`, `*.zsh` | `#` (header goes **after** the shebang line) |
| [`proto.txt`](proto.txt)   | `*.proto` | `//` |
| [`yaml.txt`](yaml.txt)     | `*.yml`, `*.yaml`, `*.toml` | `#` |

Markdown (`*.md`), JSON (`*.json`), and Jupyter notebooks (`*.ipynb`) do
**not** carry inline headers — the repository-level `LICENCE` file covers
them.

---

## Placeholders

The templates contain two placeholders that are filled in per file:

| Placeholder | Meaning | Resolution rule |
|---|---|---|
| `${years}` | Copyright year range | First commit year of the file → current year (e.g., `2024-2026`). On formatting-only edits, do not bump. |
| `${filename}` | Repo-relative path | e.g., `eda_schema/entity.py`. Update if the file is renamed or moved. |

The author and advisor lines are intentionally **hard-coded**, not
parameterized — they are project-wide invariants for the v1.x line. Add new
authors by editing the template directly.

---

## Field Semantics

- **`SPDX-License-Identifier`** — must be `CC-BY-NC-SA-4.0`. Do not change
  without a license review.
- **`SPDX-FileCopyrightText`** — copyright holder is **Drexel University,
  Integrated Circuits and Electronics (ICE) Laboratory** (institutional
  ownership, not individual).
- **`Authors`** — list of direct file contributors, append-only, in commit
  order. Removing an author requires explicit consent.
- **`Advisor`** — faculty advisor of record for the project version.
- **No `__author__` / `__copyright__` runtime attributes** — license
  metadata is a header concern only, to avoid drift.

---

## How to Apply

Manual: copy the appropriate template, paste at the top of the file
(after the shebang for shell scripts), and fill in `${years}` and
`${filename}`.

That is the entire process. No CI, no tooling, no automation pipeline —
the templates are plain text and reviewers verify the header during normal
code review.

---

## Out of Scope

- **Existing source files** — not modified by the addition of these
  templates. A bulk update is a separate, reviewable change.
- **Third-party vendored code** — keeps its upstream header; do not overwrite.
- **Generated code** (e.g., `*_pb2.py` from `protoc`) — headers must be
  injected by the generator step, not retrofitted.
