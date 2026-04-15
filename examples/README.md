# EDA-Schema Examples

Short, runnable Python scripts grouped by topic. Each module explains its purpose (look at the docstring) and, when it needs a dataset, accepts `--dataset /path/to/parquet/root` (or reads `EDA_DATASET`). For quick verification, drop a small Parquet tree under `examples/dataset/test`.

## Table of Contents

- [Directory layout](#directory-layout)
- [Getting started paths](#getting-started-paths)
- [Running examples](#running-examples)
- [Dataset-aware utilities](#dataset-aware-utilities)
- [Quick verification](#quick-verification)

## Directory layout

```
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
└── 07_database_backends/
    ├── 01_parquetdb.py
    ├── 02_filedb.py
    ├── 03_sqlitepkldb.py
    └── 04_mongodb.py

```

## Getting started paths

1. `01_basics/` for entity creation and querying  
2. `02_entities/` for deeper entity relationships  
3. `03_datasets/` for dataset workflows  
4. `04_graphs/`, `05_images/`, `06_analysis/` for intermediate workflows  
5. `07_database_backends/` for advanced integrations

## Running examples

```bash
python examples/01_basics/01_create_entities.py
python examples/03_datasets/01_load_and_inspect.py --dataset ~/datasets/nangate45
```

If a script requires data, pass `--dataset` or set `EDA_DATASET`. The documentation in each script notes dataset expectations.

## Dataset-aware utilities

Scripts like `scripts/print_netlists.py`, `scripts/list_net_pin_positions.py`, and `examples/05_images/04_routing_visualization.py` now validate the dataset path before running. Point them at any Parquet root (including `examples/dataset/test`) for consistent results.

## Quick verification

To keep the suite runnable on minimal machines, drop a small Parquet tree under `examples/dataset/test` and run:

```bash
python examples/03_datasets/01_load_and_inspect.py --dataset examples/dataset/test
python scripts/print_netlists.py --dataset examples/dataset/test
```
# EDA-Schema Examples

**Executable Python scripts for learning and automation.**

This directory contains **29+ executable Python scripts** organized by topic. These scripts are designed to be:

* **Command-line executable**: Run directly with Python
* **Copy-paste ready**: Easy to reuse in your own projects
* **Automation friendly**: Suitable for batch workflows and tooling
* **Importable**: Can be used as standalone scripts or imported as modules

---

## Prerequisites

### Required

* **EDA-schema installed**
* **Python 3.6+**
* **Basic Python knowledge**

EDA-schema installs and depends on the core scientific Python stack, including:

* NumPy
* Pandas
* Matplotlib
* NetworkX

These libraries are assumed to be available once EDA-schema is installed.

### Additional Requirements (example-dependent)

* **MongoDB** — required only for the MongoDB backend example
* **OpenROAD** — required only for OpenROAD integration examples

---

## When to Use These Examples

Use these examples when:

* You want to run code directly from the command line
* You are building scripts or tooling around EDA-schema
* You need reusable, minimal Python examples
* You want code that works without additional interactive environments

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Example Categories](#example-categories)
- [Getting Started](#getting-started)
- [Running Examples](#running-examples)
- [Quick Verification](#quick-verification)
- [Dataset-aware utilities](#dataset-aware-utilities)

---

## Example Categories

### 01_basics/ — Essential Operations

**4 examples** covering fundamental operations for beginners.
**Start here if you're new to EDA-schema.**

#### 01_create_entities.py

Creates basic tabular entities including gates, ports, pins, and nets. Demonstrates how to instantiate entities with required and optional fields.

**What you'll learn:**

* Creating `GateEntity`, `PortEntity`, `PinEntity`, and `NetEntity`
* Required vs optional fields
* Entity validation and error handling
* Accessing entity properties

---

#### 02_create_dataset.py

Creates a complete dataset from scratch, including entities, a netlist graph, and persistent storage.

**What you'll learn:**

* Initializing a `Dataset` with a database backend
* Creating and adding entities
* Building a `NetlistEntity`
* Saving data to disk
* Working with standard cell libraries

---

#### 03_load_dataset.py

Loads an existing dataset and inspects its structure.

**What you'll learn:**

* Loading datasets from disk
* Inspecting flows, stages, and entity counts
* Querying stored data
* Loading specific design flows and netlists

---

#### 04_query_data.py

Demonstrates querying and filtering entities using multiple methods.

**What you'll learn:**

* Querying by flow and stage
* Filtering with pandas DataFrames
* Accessing entities by name
* Working with tabular data
* Combining query conditions

---

### 02_entities/ — Working with Entities

**3 examples** demonstrating entity types and relationships.

#### 01_tabular_entities.py

Creates and manipulates tabular entities such as gates, ports, pins, and nets.

**What you'll learn:**

* Creating complete entity objects
* Understanding entity relationships
* Modifying entity properties
* Converting entities to tabular formats
* Validation and required fields

---

#### 02_graph_entities.py

Works with graph-based entities, primarily `NetlistEntity`.

**What you'll learn:**

* Creating netlist graphs
* Adding nodes and edges
* Traversing connectivity
* Accessing node and edge data
* Understanding node types

---

#### 03_standard_cells.py

Demonstrates working with standard cell libraries.

**What you'll learn:**

* Loading standard cells
* Accessing cell properties
* Filtering by cell type
* Using cells when creating gates
* Understanding library structure

---

### 03_datasets/ — Dataset Management

**3 examples** focused on dataset operations.

#### 01_load_and_inspect.py

Loads datasets and inspects structure and contents.

---

#### 02_filter_and_query.py

Filtering and querying dataset contents.

---

#### 03_batch_operations.py

Performs batch operations across datasets.

---

### 04_graphs/ — Graph Operations

**4 examples** for graph traversal and analysis.

---

### 05_images/ — Image Data

**4 examples** for creating and visualizing `Image2D` data.

---

### 06_analysis/ — Analysis Workflows

**4 examples** for real-world analysis tasks.

---

### 07_database_backends/ — Storage Backends

**4 examples** demonstrating supported backends.

* `ParquetDB`
* `FileDB`
* `SQLitePickleDB`
* `MongoDB`

Each example explains when and why to use the backend, along with performance and storage tradeoffs.

---


## Directory Layout

```
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
```

## Getting Started

### Beginner Path

1. `01_basics/`
2. `02_entities/`
3. `03_datasets/`

### Intermediate Path

4. `04_graphs/`
5. `05_images/`
6. `06_analysis/`

### Advanced Path

7. `07_database_backends/`

---

## Running Examples

Most examples can be run directly:

```bash
python examples/01_basics/01_create_entities.py
python examples/03_datasets/01_load_and_inspect.py --dataset ~/datasets/nangate45
```

Some examples require a dataset. Use the `--dataset` flag (or set `EDA_DATASET`) to point to a Parquet root, or drop a small test dataset under `examples/dataset/test`. Scripts will validate that the provided path exists before continuing.

## Quick Verification

To verify the example suite without the full Nangate/sky130 data, place a lightweight Parquet dataset under `examples/dataset/test`, or create a tiny dataset with the scripts in `examples/03_datasets`. Then run:

```bash
python examples/03_datasets/01_load_and_inspect.py --dataset examples/dataset/test
python scripts/print_netlists.py --dataset examples/dataset/test
```

This workflow keeps the examples runnable in CI or on machines without the large reference datasets. Adjust `--dataset` paths as needed to point to your preferred dataset root.


