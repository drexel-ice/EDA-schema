# Changelog

All notable changes to **EDA-Schema** are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Versions are tagged in Git as `vMAJOR.MINOR.PATCH`. Each release entry below
should match the version published to PyPI under the
[`eda-schema`](https://pypi.org/project/eda-schema/) distribution.

## [Unreleased]

## [2.0.0] - 2026-05-04

Major release of EDA-Schema with a redesigned multimodal datamodel, ParquetDB-backed storage, expanded OpenROAD dataset support, updated documentation, contribution policies, and release infrastructure.

### Added
- **Multimodal datamodel**: Expanded EDA-Schema beyond the original graph-only representation to support heterogeneous graphs, spatial image modalities, scalar heatmaps, and structured QoR metric entities.
- **Spatial modalities**: Added support for cell placement maps, pin placement maps, routing maps, metal-layer routing maps, clock routing maps, and PDN routing maps.
- **Scalar heatmaps**: Added support for IR drop, electromigration, and routability heatmaps.
- **QoR metrics**: Added structured support for cell, area, power, timing, and routability metrics.
- **Expanded design stages**: Added support for `place_resized` and `final` stages in addition to the v1 stages.
- **ParquetDB backend**: Added Apache Parquet based dataset storage with predicate pushdown, compressed image storage, table access helpers, and large-scale dataset support.
- **Expanded open dataset documentation**: Documented the v2 dataset scope with 18 benchmark circuits, including 16 IWLS'05 designs, OpenCores, and IBEX, across 4 open-source PDKs and 7,800+ design instances.
- **Examples and notebooks**: Added example workflows and research/tutorial notebook structure for loading, querying, analysis, and visualization.
- **Sphinx documentation**: Added documentation site structure covering the datamodel, open dataset, getting started workflows, and benchmark tasks.
- **CI workflow**: Added GitHub Actions workflow for tests and documentation builds on `main`, `dev`, and `release-v2`.
- **Community files**: Added `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`.
- **License header templates**: Added canonical Drexel ICE source-file header templates for Python, shell, Protobuf, and YAML/TOML files under `.license-headers/`.
- **Contribution guidelines**: Added development environment setup, branch conventions, commit conventions, coding standards, testing requirements, documentation requirements, and pull request checklist.
- **Security policy**: Added private vulnerability reporting process, supported-version policy, safe-harbor language, coordinated disclosure process, and security contact information.
- **Code of Conduct**: Added Contributor Covenant based community standards and enforcement guidance.

### Changed
- **README rewrite**: Reworked the README around EDA-Schema as a multimodal datamodel for digital circuit design, including feature summaries, architecture overview, installation, quick start, testing, dataset, citation, support, and license sections.
- **Project positioning**: Updated language from a graph data model schema to a broader multimodal framework covering graphs, spatial images, scalar maps, metrics, and stage-wise design evolution.
- **Development requirements**: Updated the documented Python requirement to Python 3.11+.
- **Testing workflow**: Standardized test execution through `pytest`, including unit and integration test guidance.
- **Documentation workflow**: Standardized docs builds through Sphinx under `docs/`.
- **License metadata approach**: Standardized source-file license metadata using SPDX-compatible file headers and centralized templates.
- **Repository organization**: Reorganized the project around documentation, examples, dataloaders, schema code, tests, CI, and governance files.

### Deprecated
- Deprecated the v1 `SQLitePickleDB`-centered dataset workflow in documentation in favor of the ParquetDB-backed workflow.

### Removed
- Removed the old README structure that focused only on the original graph schema and the v1 Skywater 130 nm IWLS'05 dataset.
- Removed the old documented Python 3.6+ requirement in favor of Python 3.11+.
- Removed the old quick-start example centered on `SQLitePickleDB`.
- Removed the earlier minimal `.gitignore` configuration and replaced it with a broader project-level ignore policy.

### Fixed
- Fixed incomplete changelog coverage by separating v1-only features from v2-only features.
- Fixed outdated README installation, dataset, and usage guidance.
- Fixed outdated stage documentation by including the expanded stage set.

### Security
- Added `SECURITY.md` with supported-version policy, vulnerability categories, private reporting instructions, disclosure process, safe-harbor statement, and contact channels.
- Added guidance to avoid reporting vulnerabilities through public Issues.
- Added repository policy language for accidental exposure of credentials, internal hostnames, private dataset paths, and PII.
- Added contribution checklist guidance to prevent secrets, credentials, internal hostnames, or proprietary data from being included in pull requests.
- Added license header templates with SPDX identifiers to improve license scanning and source-file provenance.

## [1.0.0] - 2023-02-03

Initial public release of EDA-Schema, a graph data model schema and open dataset framework for digital design automation research.

### Added
- **Package**: Initial release of the `eda-schema` Python package.
- **Graph datamodel**: Property graph data model for representing digital circuit designs and associated attributes.
- **Netlist graph representation**: Graph structure for IO pins, gates, wires, nets, and connectivity entities.
- **Timing path graph representation**: Graph structure for timing paths extracted from the EDA flow.
- **Interconnect graph representation**: Graph structure for interconnect-related circuit data.
- **Clock tree structures**: Clock-related graph structures for circuit analysis.
- **Design-stage snapshots**: Support for physical design stages `floorplan`, `global_place`, `detailed_place`, `cts`, `global_route`, and `detailed_route`.
- **Circuit metrics**: Support for tabular design metadata and associated circuit metrics.
- **Dataset loading workflow**: Dataset loading through the documented `Dataset` and `SQLitePickleDB` interfaces.
- **Open dataset documentation**: Documentation for the OpenROAD and Skywater 130 nm based dataset generated from selected IWLS'05 benchmark circuits.
- **Benchmark circuit documentation**: Documented benchmark set including `ac97_ctrl`, `aes_core`, `des3_area`, `i2c`, `mem_ctrl`, `pci`, `sasc`, `simple_spi`, `spi`, `ss_pcm`, `systemcaes`, `systemcdes`, `tv80`, `usb_funct`, `usb_phy`, and `wb_dma`.
- **Post-routed dataset summary**: Documented 32 total circuit instances, 148,687 gates excluding fillers and tap cells, 148,337 nets, 125,256 timing paths, and approximately 23 GB of data.
- **Project files**: Package setup, development requirements, tests, notebooks, scripts, schema files, and supporting documentation.

### Changed
- Established the initial package metadata for version `1.0.0`.
- Organized the repository around schema code, protocol definitions, notebooks, scripts, tests, and documentation.
- Standardized the documented workflow for loading EDA-Schema datasets from a local dataset directory.

### Deprecated
- No deprecated APIs or schema entities are included in this release.

### Removed
- No APIs, files, schema entities, or dataset components were removed in this release.

### Fixed
- No bug fixes are included because this is the initial public release.

### Security
- No security changes are included because this is the initial public release.

[Unreleased]: https://github.com/drexel-ice/eda-schema/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/drexel-ice/eda-schema/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/drexel-ice/eda-schema/releases/tag/v1.0.0
