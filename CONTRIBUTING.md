# Contributing to EDA-Schema

Thank you for your interest in contributing to **EDA-Schema** — a multimodal
property-graph datamodel and open dataset for digital circuit physical design,
maintained by the [Drexel University Integrated Circuits and Electronics (ICE)
Laboratory](https://github.com/drexel-ice).

This guide is the contract for code, documentation, and dataset contributions.
Pull requests that do not follow these guidelines will be asked to revise
before review.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [License of Contributions](#license-of-contributions)
3. [Ways to Contribute](#ways-to-contribute)
4. [Development Environment](#development-environment)
5. [Branch and Commit Conventions](#branch-and-commit-conventions)
6. [Coding Standards](#coding-standards)
7. [Standardized File Header (Drexel ICE)](#standardized-file-header-drexel-ice)
8. [Testing](#testing)
9. [Documentation](#documentation)
10. [Pull Request Checklist](#pull-request-checklist)
11. [Reporting Bugs](#reporting-bugs)
12. [Security Issues](#security-issues)
13. [Maintainers and Contact](#maintainers-and-contact)

---

## Code of Conduct

This project adheres to the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).
By participating, you agree to uphold this code. Report unacceptable behavior
to **ps937@drexel.edu**, **aja367@drexel.edu** or **is338@drexel.edu**.

---

## License of Contributions

EDA-Schema is licensed under the
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0)](LICENCE) license.

By submitting a contribution (pull request, patch, dataset, documentation,
or example) you agree that:

1. Your contribution is your original work or you have the right to submit it.
2. Your contribution is licensed under the same **CC BY-NC-SA 4.0** terms as
   the rest of the project.
3. You will not be paid for your contribution and grant the maintainers the
   right to redistribute it under the project license.
4. Derivative works must remain non-commercial and must be shared under the
   same license (ShareAlike).

If your employer holds intellectual property rights to your work, obtain
written permission before contributing.

---

## Ways to Contribute

| Type | Examples | Where |
|---|---|---|
| **Bug reports** | Incorrect parsing, schema mismatch, dataset errors | [GitHub Issues](https://github.com/drexel-ice/eda-schema/issues) |
| **Feature requests** | New entities, modalities, query APIs | [GitHub Discussions](https://github.com/drexel-ice/eda-schema/discussions) |
| **Code patches** | Bug fixes, performance, new backends | Pull Request |
| **Documentation** | Schema docs, tutorials, API reference | Pull Request |
| **Dataset extensions** | Additional circuits, PDKs, design corners | Coordinate with maintainers first |
| **Research notebooks** | Reproducible analyses under `research/notebooks/` | Pull Request |

Open an Issue **before** starting work on a non-trivial change so it can be
scoped and assigned.

---

## Development Environment

### Prerequisites

- Python **3.11+** (matches `setup.py` `python_requires=">=3.11"`)
- Git
- 8 GB+ RAM recommended for full dataset workflows
- Optional: Graphviz (graph visualization), `pre-commit`

### Setup

```bash
git clone https://github.com/drexel-ice/eda-schema.git
cd eda-schema

python3 -m venv .venv
source .venv/bin/activate

pip install -e .[dev]
```

This installs the package in editable mode along with the development
dependencies declared in `requirements-dev.txt`.

---

## Branch and Commit Conventions

### Branches

- `dev` — primary integration branch (default base for PRs).
- `release-vX.Y.Z-*` — release-prep branches.
- `feature/<short-description>` — new functionality.
- `fix/<short-description>` — bug fixes.
- `docs/<short-description>` — documentation-only changes.

### Commit messages

Follow the [Conventional Commits 1.0](https://www.conventionalcommits.org/)
style:

```
<type>(<scope>): <short summary>

<body explaining the why, not the what>

<footer with issue refs, breaking-change notices>
```

Allowed `<type>` values: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, `revert`.

Example:

```
feat(entity): add NetArc capacitance fields

Adds C_total and C_couple fields to NetArcEntity to support
parasitic-aware timing analyses requested in #42.

Refs: #42
```

---

## Coding Standards

| Aspect | Standard |
|---|---|
| Style | [PEP 8](https://peps.python.org/pep-0008/), 100-column soft limit |
| Formatting | `black` (default config) |
| Imports | `isort` (`black` profile) |
| Linting | `ruff` (project config in `pyproject.toml` once added) |
| Typing | [PEP 484](https://peps.python.org/pep-0484/) annotations on all public APIs |
| Docstrings | [PEP 257](https://peps.python.org/pep-0257/) / NumPy style |
| Naming | `snake_case` for functions/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants |
| Schema fields | Match the canonical names in `docs/datamodel.rst` — flag any divergence in the PR |

Run before pushing:

```bash
black eda_schema tests
isort eda_schema tests
ruff check eda_schema tests
pytest
```

---

## Standardized File Header (Drexel ICE)

> **Status:** Proposed — not yet applied to existing sources. Apply to **new**
> files immediately; existing files will be migrated in a single sweep tracked
> in `CHANGELOG.md`.

Every Python source file (`.py`), shell script (`.sh`), and Protobuf file
(`.proto`) shipped with the project must begin with the following header.

### Python / `.py`

```python
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2024-2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema — Multimodal datamodel for digital circuit design
# Module  : <relative path, e.g. eda_schema/entity.py>
# Authors : Pratik Shrestha       <ps937@drexel.edu>
#           Alec Aversa           <aja367@drexel.edu>
# Advisor : Ioannis Savidis       <is338@drexel.edu>
#
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike
# 4.0 International License (CC BY-NC-SA 4.0). You may obtain a copy of the
# license at: https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. Commercial use is
# expressly prohibited; derivative works must be shared under the same
# license terms (ShareAlike).
```

### Shell / `.sh`

```bash
#!/usr/bin/env bash
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2024-2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema
# Script  : <relative path>
# Authors : Pratik Shrestha <ps937@drexel.edu>, Alec Aversa <aja367@drexel.edu>
# Advisor : Ioannis Savidis <is338@drexel.edu>
#
# Licensed under CC BY-NC-SA 4.0. See LICENCE for full terms.
# Non-commercial use only; ShareAlike required for derivative works.
```

### Protobuf / `.proto`

```protobuf
// SPDX-License-Identifier: CC-BY-NC-SA-4.0
// SPDX-FileCopyrightText: Copyright (c) 2024-2026 Drexel University,
//                         Integrated Circuits and Electronics (ICE) Laboratory
//
// Project : EDA-Schema
// File    : <relative path>
// Authors : Pratik Shrestha <ps937@drexel.edu>, Alec Aversa <aja367@drexel.edu>
// Advisor : Ioannis Savidis <is338@drexel.edu>
//
// Licensed under CC BY-NC-SA 4.0. See LICENCE for full terms.
```

### Field rules

- **Year range** — start year is the file's first commit year; end year is the
  current year. Update on substantive edits, not formatting passes.
- **`Module` / `Script` / `File` line** — relative path from repo root; keep
  in sync if the file is renamed or moved.
- **`Authors` line** — list direct contributors to the file in commit order;
  do **not** remove prior authors.
- **SPDX identifiers** — required for automated license scanners (REUSE,
  ScanCode, FOSSology). Do not change the identifier without a license review.
- **No `__author__` / `__copyright__` runtime variables** — keep license info
  in the header only, not in module attributes.

---

## Testing

```bash
pytest                       # full suite
pytest tests/unit/           # fast unit tests
pytest tests/integration/    # integration tests (may require dataset)
pytest -k "<expression>"     # subset by name
```

Requirements for new code:

1. **Coverage** — every new public function/class must have at least one unit
   test.
2. **Fixtures** — use `tests/conftest.py` fixtures rather than ad-hoc setup.
3. **No network calls** — tests must run offline; mock external services.
4. **No real dataset writes** — use `tmp_path` and synthetic ParquetDB
   instances.
5. **Determinism** — seed any randomness; avoid `time.time()` in assertions.

---

## Documentation

- Schema documentation lives under `docs/` and is built with Sphinx + MyST:

  ```bash
  cd docs
  make html
  ```

- Update `docs/datamodel.rst` whenever you add or change a schema entity.
- Add or update an example under `examples/` for any new public API.
- Keep `README.md`, `docs/`, and `CHANGELOG.md` consistent — a feature is not
  "done" until all three reflect it.

---

## Pull Request Checklist

Before opening a PR, confirm:

- [ ] Branch is rebased on the latest `dev`.
- [ ] Commits follow Conventional Commits.
- [ ] New / changed files carry the [Drexel ICE header](#standardized-file-header-drexel-ice).
- [ ] `black`, `isort`, `ruff`, and `pytest` pass locally.
- [ ] Docstrings and type annotations are present on public APIs.
- [ ] `CHANGELOG.md` `[Unreleased]` section is updated.
- [ ] Documentation under `docs/` is updated for user-visible changes.
- [ ] No secrets, credentials, internal hostnames, or proprietary data are
      included.
- [ ] PR description references the related Issue (e.g. `Closes #123`).

PRs are reviewed by an ICE Lab maintainer. Expect at least one round of
feedback. Large changes may be split into smaller PRs at the maintainer's
request.

---

## Reporting Bugs

File bugs at <https://github.com/drexel-ice/eda-schema/issues> using the
following template:

```
**Environment**
- eda-schema version:
- Python version:
- OS:

**Expected behavior**
…

**Actual behavior**
…

**Reproduction**
Minimal code snippet or dataset reference.

**Logs / traceback**
…
```

---

## Security Issues

Do **not** file security vulnerabilities as public Issues.
Follow the disclosure process in [`SECURITY.md`](SECURITY.md).

---

## Maintainers and Contact

| Role | Name | Email |
|---|---|---|
| Author | Pratik Shrestha | ps937@drexel.edu |
| Author | Alec Aversa | aja367@drexel.edu |
| Faculty advisor | Ioannis Savidis | is338@drexel.edu |
| Lab | Drexel ICE Laboratory | https://github.com/drexel-ice |

For coordination of larger contributions (new datasets, new modalities,
sponsored research), email the lead author and advisor before opening a PR.
