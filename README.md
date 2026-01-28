# EDA-Schema: A Property Graph Data Model for Digital Circuit Design

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/eda-schema.svg)](https://pypi.org/project/eda-schema/)

EDA-Schema is an open, standardized, and extensible data model and framework for representing, storing, and analyzing digital circuit physical design data across the RTL-to-GDSII flow. It models circuits using property graphs and spatial image modalities, providing standardized representations of circuit structure, performance metrics, and design evolution, and enabling consistent analysis, reproducibility, and machine learning research in electronic design automation.

## Key Features

- Unified Data Model: Standardized property graph representation of digital circuits
- High Performance: Optimized columnar storage with predicate pushdown and parallel processing
- ParquetDB Backend: Efficient Apache Parquet-based storage for large-scale EDA datasets
- Rich Analytics: Built-in analysis tools for timing, power, area, and routability
- Open Dataset: 32 benchmark circuits from IWLS'05 suite processed with OpenROAD
- Research Ready: Extensible framework for ML and optimization research

## Table of Contents

- [Data Model Overview](#data-model-overview)
- [Open Dataset](#open-dataset)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Testing & Development](#testing--development)
- [Citation](#citation)
- [Support & Contact](#support--contact)

---

## Data Model Overview

### Schema Architecture

EDA-Schema is a property graph data-model schema for representing digital circuits across the RTL-to-GDSII physical design flow. At each design stage, netlists and analysis reports are used to capture structural information, performance metrics, and spatial layout data, which become increasingly complete and accurate as the flow progresses.

Each circuit is represented using property graphs and spatial image modalities. Graphs model logical, physical, and timing relationships among gates, pins, nets, and I/O ports, while image representations capture placement, routing, clock networks, power delivery, and analysis heatmaps. Together, these modalities form the core of the EDA-Schema datamodel.

### Primary Graph Entities

| Entity                 | Description                                                                               | Nodes                                                              | Edges                                                              |
| ---------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| **Netlist Graph**      | Complete logical and physical representation of circuit connectivity                      | Gates, pins, nets, I/O ports                                       | Logical connections, physical interconnect connectivity            |
| **Timing Path Graph**  | Directed representation of signal propagation paths extracted from static timing analysis | Pins, I/O ports, cell timing arcs, net timing arcs                 | Signal propagation between successive timing elements              |
| **Clock Tree Graph**   | Subgraph modeling clock distribution from source to sequential elements                   | Clock source ports, clock buffers, pins, nets, sequential elements | Clock signal propagation and distribution connections              |
| **Interconnect Graph** | Physical routing and parasitic modeling of nets after placement and routing               | Nets, routing segments, pins                                       | Routed wire segments with resistance and capacitance relationships |

### Supporting Tabular Entities

In addition to graph-structured data, EDA-Schema includes a set of tabular entities that store attributes, metrics, and metadata associated with each graph and design stage.

| Category                              | Entities                                                                 | Purpose                                                                                                                                        |
| ------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Design Flow and Constraints**       | DesignFlow, DesignStage, DesignConstraint                                | Track a full RTL to GDSII run, per-stage artifacts, and SDC-style constraints such as clock period, I/O delays, utilization, and aspect ratio  |
| **Circuit Elements**                  | GateInstance, Net, Pin, Port                                             | Store instance-level and connection-level attributes such as placement bounds, fanout, parasitics, and pin timing attributes                   |
| **Library and Cell Characterization** | StandardCell                                                             | Capture technology library attributes and cell characterization needed to interpret instances and timing behavior                              |
| **Timing Path Components**            | TimingPath, CellArc, NetArc                                              | Represent STA-derived timing path structure and per-arc delay and slew contributions                                                           |
| **Quality Metrics**                   | CellMetrics, AreaMetrics, PowerMetrics, TimingMetrics, RoutabilityMetric | Provide stage-wise QoR metrics for analysis and ML labels, including power, area, slack and RUDY-based routability maps                        |


### Design Stages Captured

1. **floorplan**: Initial floorplanning and IO placement
2. **global_place**: Global placement optimization
3. **place_resized**: Cell sizing for timing/area
4. **detailed_place**: Legalization and detailed placement
5. **cts**: Clock tree synthesis completion
6. **global_route**: Global routing with congestion analysis
7. **detailed_route**: Final routing with parasitic extraction

![EDA-Schema Entity Relationship Diagram](docs/images/schema.png)

---


## Open Dataset

EDA-Schema provides an open and reproducible dataset of digital physical designs generated using open-source tools, public benchmark circuits, and multiple open process design kits. The dataset captures stage-wise circuit representations across the OpenROAD physical design flow and is expanded through systematic parameter sweeps.

### Dataset Specifications

* **Physical Design Toolset**: OpenROAD

* **Design PDKs**:

  * Nangate 45 nm
  * SkyWater 130 nm
  * ASAP7 7 nm
  * IHP SG13G2 130 nm

* **Flow Stages** (OpenROAD stage naming used by the schema):

  * floorplan, global_place, place_resize, detailed_place, cts, global_route, detailed_route, final

### Timing Operating Points

V2 does not use fixed global values for clock latency or delays. Instead, constraints are defined relative to the target clock period, and designs are generated near timing closure.

* **Barely-Fail and Barely-Pass Definition** (using Slack-to-Clock-Period Ratio, SCPR):

  * Barely-Fail: SCPR in (-10%, 0%)
  * Barely-Pass: SCPR in (0%, +10%)

* **Baseline Operating Point Defaults**:

  * Aspect ratio fixed at 1.0
  * Placement density assumed uniform
  * Core utilization:

    * 40% for ASAP7 and Nangate 45 nm
    * 30% for SkyWater 130 nm and IHP SG13G2 130 nm

* **Clocking and I/O Constraints**:

  * Input and output delays: 20% of target clock period
  * Clock latency: 1% of target clock period, capped at 50 ps
  * Clock uncertainty: 5% of target clock period, capped at 250 ps

### Dataset Expansion

To increase diversity and capture realistic design trade-offs, the dataset is expanded using parameter sweeps:

* Target clock periods: {0.8 x BF, BF, BP, 1.2 x BP}
* Aspect ratio: {0.5, 1.0, 1.5}
* Core utilization: PDK-dependent ranges
* Placement density: uniform, 1.25x uniform, 1.5x uniform

### Download

**Dataset**: [Google Drive (23GB)](https://drive.google.com/drive/folders/1B3rBvbnviBrKw1aLRpv7e1pEXSCy_vLQ?usp=sharing)

---

## Installation

### System Requirements

- Python: 3.10 or higher
- Memory: 8GB+ recommended for large datasets

### Quick Install

```bash
# Clone repository
git clone https://github.com/drexel-ice/eda-schema.git
cd eda-schema

# Install with pip
pip install -e .
```

### Platform-Specific Setup

#### Linux/macOS (Intel)
```bash
# Graphviz for visualization (optional)
export CFLAGS="-I$(brew --prefix graphviz)/include"
export LDFLAGS="-L$(brew --prefix graphviz)/lib"
pip install pygraphviz
```

#### macOS (Apple Silicon)
```bash
# Graphviz for Apple Silicon
pip install --no-cache-dir \
    --global-option=build_ext \
    --global-option="-I/opt/homebrew/include" \
    --global-option="-L/opt/homebrew/lib" \
    pygraphviz
```

#### Optional Dependencies

```bash
# Additional dependencies for enhanced performance
pip install -r dev_requirements.txt
```

### Verification

```bash
# Run tests
pytest

# Quick validation
python -c "import eda_schema; print('EDA-Schema installed successfully!')"
```

---

## Quick Start

### Load and Explore Dataset

```python
from eda_schema.dataset import Dataset
from eda_schema.db.parquet import ParquetDB

# Connect to ParquetDB dataset
db = ParquetDB("/path/to/iwls05_dataset")
dataset = Dataset(db)

# Explore structure
flows = dataset.get_design_flows()
print(f"Available flows: {len(flows)}")

# Load timing data
timing_data = dataset.get_table_data("timing_metrics", stage="detailed_route")
print(f"Worst slack: {timing_data.worst_slack.min():.3f} ns")

# Analyze netlist graph
netlist = dataset.get_graph_data("netlist", stage="cts")
print(f"Circuit size: {netlist.number_of_nodes()} nodes, {netlist.number_of_edges()} edges")
```

### Performance Analysis

```python
import matplotlib.pyplot as plt

# Compare timing across stages
stages = ["floorplan", "cts", "detailed_route"]
slack_values = []

for stage in stages:
    timing = dataset.get_table_data("timing_metrics", stage=stage)
    worst_slack = timing.worst_slack.min()
    slack_values.append(worst_slack)
    print(f"{stage}: {worst_slack:.3f} ns")

# Visualize timing evolution
plt.plot(stages, slack_values, 'o-')
plt.ylabel('Worst Slack (ns)')
plt.title('Timing Convergence Across Design Flow')
plt.grid(True, alpha=0.3)
plt.show()
```

---

## Usage Examples

### Basic Operations

```python
# 1. Create entities
from eda_schema import entity

gate = entity.GateEntity(
    name="NAND2_X1",
    flow_id="flow_001",
    stage="cts",
    x=10.5, y=20.3,
    width=1.2, height=1.8,
    standard_cell_name="NAND2_X1"
)

# 2. Query data with filters
timing_critical = dataset.get_table_data(
    "timing_metrics",
    stage="detailed_route",
    filters={"worst_slack": lambda x: x < -0.05}
)

# 3. Graph analysis
netlist_graph = dataset.get_graph_data("netlist", stage="cts")

# Find high-fanout nets
fanout_counts = dict(netlist_graph.degree())
high_fanout = {node: deg for node, deg in fanout_counts.items() if deg > 10}
```

### Advanced Analytics

```python
# Timing path analysis
timing_paths = dataset.get_graph_data("timing_paths", stage="detailed_route")

# Calculate path length distribution
path_lengths = [len(path) for path in timing_paths.edges()]
plt.hist(path_lengths, bins=20, alpha=0.7)
plt.xlabel('Timing Path Length')
plt.ylabel('Frequency')
plt.title('Distribution of Timing Path Lengths')
plt.show()

# Power consumption trends
power_data = dataset.get_table_data("power_metrics")
stages = ["floorplan", "global_place", "cts", "detailed_route"]

for stage in stages:
    stage_power = power_data[power_data.stage == stage]
    total_power = stage_power.total_power.sum()
    print(f"{stage}: {total_power:.2f} μW")
```

---

## Testing & Development

### Run Test Suite

```bash
# All tests
pytest

# Specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests

# With coverage
pytest --cov=eda_schema --cov-report=html
```

### Code Quality

```bash
# Linting
pylint eda_schema/

# Formatting
black --check .
black .

# Type checking
mypy eda_schema/
```

### Development Setup

```bash
# Install development dependencies
pip install -r dev_requirements.txt

# Generate protocol buffers
./generate_proto.sh

# Build documentation
cd docs && make html
```

---

## Citation

If you use EDA-Schema in your research, please cite our work:

```bibtex
@inproceedings{shrestha2024eda,
  title={EDA-schema: A graph datamodel schema and open dataset for digital design automation},
  author={Shrestha, Prateek and Aversa, Rocco and Phatharodom, Saranyu and Savidis, Ioannis},
  booktitle={Proceedings of the ACM Great Lakes Symposium on VLSI (GLSVLSI)},
  pages={69--77},
  year={2024}
}
```

---

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/drexel-ice/eda-schema/issues)
- **Discussions**: [GitHub Discussions](https://github.com/drexel-ice/eda-schema/discussions)
- **Email**: Prateek Shrestha (ps937@drexel.edu)
- **Advisor**: Ioannis Savidis (is338@drexel.edu)

### Troubleshooting

**Common Issues:**

1. **Memory Errors**: Use column selection and batch processing for large datasets
2. **Import Errors**: Ensure all dependencies are installed with `pip install -e .`
3. **PyArrow Compatibility**: Use PyArrow 10.0+ for optimal performance
4. **Graphviz Issues**: Install system graphviz before pygraphviz

**Performance Tips:**

- Use `ParquetDB` for large datasets with frequent queries
- Enable predicate pushdown for selective data access
- Use parallel processing for I/O-bound operations
- Use ParquetDB for optimal performance with large EDA datasets

---
