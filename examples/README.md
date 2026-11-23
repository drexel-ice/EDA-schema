# EDA-Schema Examples

Executable Python scripts for learning, automation, and dataset workflows.

This directory contains runnable Python examples organized by topic. Each script is designed to be:

* Command-line executable
* Copy-paste ready
* Automation friendly
* Importable as a standalone module

## Table of Contents

- [Prerequisites](#prerequisites)
- [Directory Layout](#directory-layout)
- [Example Categories](#example-categories)
- [Getting Started](#getting-started)
- [Running Examples](#running-examples)
- [Dataset-Aware Utilities](#dataset-aware-utilities)
- [Quick Verification](#quick-verification)

## Prerequisites

### Required

* EDA-Schema installed
* Python 3.6+
* Basic Python knowledge

EDA-Schema installs and depends on the core scientific Python stack, including:

* NumPy
* Pandas
* Matplotlib
* NetworkX

### Additional Requirements

Some examples require additional tools:

* MongoDB, required only for the MongoDB backend example
* OpenROAD, required only for OpenROAD integration examples

## Directory Layout

```text
examples
├── 01_basics/
│   ├── 01_create_entities.py
│   ├── 02_create_dataset.py
│   ├── 03_load_dataset.py
│   └── 04_query_data.py
├── 02_entities/
│   ├── 01_tabular_entities.py
│   ├── 02_graph_entities.py
│   └── 03_standard_cells.py
├── 03_datasets/
│   ├── 01_load_and_inspect.py
│   ├── 02_filter_and_query.py
│   └── 03_batch_operations.py
├── 04_graphs/
│   ├── 01_netlist_traversal.py
│   ├── 02_timing_paths.py
│   ├── 03_clock_trees.py
│   └── 04_graph_analysis.py
├── 05_images/
│   ├── 01_create_images.py
│   ├── 02_plot_images.py
│   ├── 03_placement_visualization.py
│   └── 04_routing_visualization.py
├── 06_analysis/
│   ├── 01_compare_stages.py
│   ├── 02_power_analysis.py
│   ├── 03_timing_analysis.py
│   └── 04_area_analysis.py
├── 07_database_backends/
│   ├── 01_parquetdb.py
│   ├── 02_filedb.py
│   ├── 03_sqlitepkldb.py
│   └── 04_mongodb.py
└── 08_mcp/
    ├── 01_inprocess_client.py
    ├── 02_stdio_client.py
    ├── 03_render_images.py
    └── mcp.json
```

## Example Categories

### 01_basics

Essential operations for new users.

#### 01_create_entities.py

Creates basic tabular entities, including gates, ports, pins, and nets.

What you will learn:

* Creating `GateEntity`, `PortEntity`, `PinEntity`, and `NetEntity`
* Understanding required and optional fields
* Entity validation and error handling
* Accessing entity properties

#### 02_create_dataset.py

Creates a complete dataset from scratch, including entities, a netlist graph, and persistent storage.

What you will learn:

* Initializing a `Dataset` with a database backend
* Creating and adding entities
* Building a `NetlistEntity`
* Saving data to disk
* Working with standard cell libraries

#### 03_load_dataset.py

Loads an existing dataset and inspects its structure.

What you will learn:

* Loading datasets from disk
* Inspecting flows, stages, and entity counts
* Querying stored data
* Loading specific design flows and netlists

#### 04_query_data.py

Demonstrates querying and filtering entities using multiple methods.

What you will learn:

* Querying by flow and stage
* Filtering with pandas DataFrames
* Accessing entities by name
* Working with tabular data
* Combining query conditions

### 02_entities

Entity types and relationships.

#### 01_tabular_entities.py

Creates and manipulates tabular entities such as gates, ports, pins, and nets.

What you will learn:

* Creating complete entity objects
* Understanding entity relationships
* Modifying entity properties
* Converting entities to tabular formats
* Validation and required fields

#### 02_graph_entities.py

Works with graph-based entities, primarily `NetlistEntity`.

What you will learn:

* Creating netlist graphs
* Adding nodes and edges
* Traversing connectivity
* Accessing node and edge data
* Understanding node types

#### 03_standard_cells.py

Demonstrates working with standard cell libraries.

What you will learn:

* Loading standard cells
* Accessing cell properties
* Filtering by cell type
* Using cells when creating gates
* Understanding library structure

### 03_datasets

Dataset loading, filtering, querying, and batch operations.

Examples:

* `01_load_and_inspect.py`
* `02_filter_and_query.py`
* `03_batch_operations.py`

### 04_graphs

Graph traversal and analysis.

Examples:

* `01_netlist_traversal.py`
* `02_timing_paths.py`
* `03_clock_trees.py`
* `04_graph_analysis.py`

### 05_images

Creating and visualizing `Image2D` data.

Examples:

* `01_create_images.py`
* `02_plot_images.py`
* `03_placement_visualization.py`
* `04_routing_visualization.py`

### 06_analysis

Analysis workflows for real-world EDA tasks.

Examples:

* `01_compare_stages.py`
* `02_power_analysis.py`
* `03_timing_analysis.py`
* `04_area_analysis.py`

### 07_database_backends

Supported storage backend examples.

Examples:

* `01_parquetdb.py`
* `02_filedb.py`
* `03_sqlitepkldb.py`
* `04_mongodb.py`

Each backend example explains when to use the backend, why it is useful, and the relevant performance and storage tradeoffs.

### 08_mcp

Using the MCP server, which exposes one per-PDK dataset to LLM agents. These examples need `pip install -e ".[mcp]"` or the `docker/mcp` image.

Examples:

* `01_inprocess_client.py`: call the tools through an in-process MCP client
* `02_stdio_client.py`: start the server over stdio, as Claude Code would, and save a rendered routing map
* `03_render_images.py`: save every image of one stage as the PNG an agent receives
* `mcp.json`: client configuration, for a local install and for Docker

See `docs/mcp.rst` for the full guide.

## Getting Started

### Beginner Path

1. `01_basics/`
2. `02_entities/`
3. `03_datasets/`

### Intermediate Path

1. `04_graphs/`
2. `05_images/`
3. `06_analysis/`

### Advanced Path

1. `07_database_backends/`
2. `08_mcp/`

## Running Examples

Most examples can be run directly:

```bash
python examples/01_basics/01_create_entities.py
python examples/03_datasets/01_load_and_inspect.py --dataset ~/datasets/nangate45
```

Some examples require a dataset. Use the `--dataset` flag or set the `EDA_DATASET` environment variable to point to a Parquet root.

Example:

```bash
export EDA_DATASET=~/datasets/nangate45
python examples/03_datasets/01_load_and_inspect.py
```

## Dataset-Aware Utilities

The following utilities validate the dataset path before running:

* `scripts/print_netlists.py`
* `scripts/list_net_pin_positions.py`
* `examples/05_images/04_routing_visualization.py`

Point these scripts at any Parquet root, including `examples/dataset/test`, for consistent results.

## Quick Verification

To verify the examples without the full Nangate or Sky130 datasets, place a lightweight Parquet dataset under:

```text
examples/dataset/test
```

Then run:

```bash
python examples/03_datasets/01_load_and_inspect.py --dataset examples/dataset/test
python scripts/print_netlists.py --dataset examples/dataset/test
```

This workflow keeps the examples runnable in CI or on machines without large reference datasets. Adjust `--dataset` paths as needed for your environment.
