# Changelog

All notable changes to **EDA-Schema** are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Versions are tagged in Git as `vMAJOR.MINOR.PATCH`. Each release entry below
should match the version published to PyPI under the
[`eda-schema`](https://pypi.org/project/eda-schema/) distribution.

## [Unreleased]

### Added
- Community health files: `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
- Standardized Drexel ICE source-file header proposal (see `CONTRIBUTING.md`).

### Changed
- _None_

### Deprecated
- _None_

### Removed
- _None_

### Fixed
- _None_

### Security
- _None_

## [1.0.0] — 2026-05-03

Initial public release of the EDA-Schema multimodal datamodel and dataset tooling.

### Added
- **Datamodel** — Heterogeneous graph schema for digital circuits across the
  RTL→GDSII flow (netlist, clock network, timing path, power delivery network)
  with structured QoR metric entities (cell, area, power, timing, routability).
- **Spatial modalities** — Cell/pin/routing placement maps, metal-layer routing
  maps, clock and PDN routing maps; scalar heatmaps for IR drop,
  electromigration, and routability (RUDY).
- **Stage-resolved snapshots** — `floorplan`, `global_place`, `place_resized`,
  `detailed_place`, `cts`, `global_route`, `detailed_route`, `final`.
- **Storage backend** — ParquetDB (Apache Parquet) with predicate pushdown and
  parallel processing for large-scale datasets.
- **Open dataset** — 18 benchmark circuits (16 IWLS'05, OpenCores, IBEX),
  4 open-source PDKs, 7,800+ design instances; distributed via Google Drive.
- **Examples** — End-to-end loading and query examples under `examples/`.
- **Documentation** — Sphinx (MyST) site under `docs/` covering datamodel,
  open dataset, getting started, and benchmark tasks.
- **Tests** — Unit and integration suites under `tests/`.
- **CI** — GitHub Actions workflow at `.github/workflows/ci.yml`.

[Unreleased]: https://github.com/drexel-ice/eda-schema/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/drexel-ice/eda-schema/releases/tag/v1.0.0
