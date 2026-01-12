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

### 08_integration/ — External Integration

**3 examples** for integrating with external tools and formats.

* Importing OpenROAD designs
* Exporting to Protocol Buffers
* Writing custom data loaders

---

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
8. `08_integration/`

---

## Running Examples

Most examples can be run directly:

```bash
python examples/01_basics/01_create_entities.py
```

Some examples require a dataset, which you can either create or point to an existing directory.
