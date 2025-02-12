# EDA-schema

EDA-schema is a property graph datamodel schema developed to represent digital circuit designs and the associated attributes.
The contributions of this work include:
1. A standardized set of graph structures and feature sets representing a digital circuit and corresponding subcomponents
2. A dataset of physical designs generated from the IWLS'05 benchmark circuit suite utilizing the open-source 130 nm Process Design Kit (PDK) provided by Skywater and the open-source toolset OpenROAD

NOTE: This GitHub repository is still in the development phase. We are actively working on adding new features, fixing bugs, and enhancing the overall functionality. We appreciate your patience and understanding as we work to finalize the project.


## Graph Datamodel Schema

EDA-schema is a property graph data-model schema used to represent digital circuits. Netlists and performance reports are extracted from design tools after each stage of the EDA design flow. These files are utilized to derive structural information and performance metrics for each phase. While post-routing netlists and performance metrics are final and complete, earlier stages still provide incomplete yet useful structural information and estimated performance metrics. The data becomes more complete and accurate as the design flow progresses.

A circuit extracted from the design flow is represented as a graph where nodes are IO pins, gates, and wires, and edges are the connections between them. This primary netlist graph representation is complemented by more granular graph representations, such as a timing path graph and an interconnect graph. Together, these representations complete the schema.

Presented is the entity relationship diagram (ERD) of EDA-schema. The primary graph entities—netlist, clock tree, timing path, and interconnect graphs—are highlighted in gold. Additional tabular entities associated with each graph are shown in silver. For each circuit, a snapshot of data is available for the following design stages/phases.
- Post floorplan: floorplan
- Post global placement: global_place
- Post detailed placement: detailed_place
- Post CTS: cts
- Post global routing: global_route
- Post detailed routing: detailed_route


![Alt text](docs/images/schema.png)

## Open Dataset
A comprehensive dataset for physical design is comprised of four key components:
1) Design circuits: selected [IWLS'05 benchmark circuits](https://github.com/ieee-ceda-datc/RDF-2020/tree/master/benchmarks/iwls05_opencores)
2) Process Development Kit (PDK): [Skywater 130 nm](https://skywater-pdk.readthedocs.io/en/main/)
3) Physical Design Toolset: [OpenROAD](https://theopenroadproject.org/)
4) Design parameters and Constraints:
    - clock latency: 0.01 ns
    - clock input delay: 0.01
    - clock output delay: 0.01
    - utilization: 30%
    - aspect ratio: 1.0
    - clock uncertainty (setup/hold): 0.2ns


Following circuits are used under target clock to meet/barely miss timing.

|         | Barely Fail (id=000001) | |  Barely Pass (id=000002) | |
|---|---|---|---|---|
| **Circuit** | **Target Clock Period (ns)** | **Worst Slack (ns)** | **Target Clock Period (ns)** | **Worst Slack (ns)** |
|ac97_ctrl | 3 | -0.1823 | 3.25 | 0.1333|
|aes_core | 3.5 | -0.1999 | 3.75 | 0.0458|
|des3_area | 3.75 | -0.0119 | 4 | 0.1823|
|i2c | 2.25 | -0.1594 | 2.5 | 0.0658|
|mem_ctrl | 5 | -0.0863 | 5.25 | 0.1420|
|pci | 3.75 | -0.1326 | 4 | 0.1548|
|sasc | 1.75 | -0.0992 | 2 | 0.1752|
|simple_spi | 2 | -0.1452 | 2.25 | 0.1232|
|spi | 4.25 | -0.1739 | 4.5 | 0.2488|
|ss_pcm | 1.625 | -0.0144 | 1.75 | 0.1107|
|systemcaes | 4.75 | -0.1644 | 5 | 0.0050|
|systemcdes | 4 | -0.0069 | 4.25 | 0.3052|
|tv80 | 7 | -0.0294 | 7.25 | 0.1227|
|usb_funct | 2.5 | -0.0917 | 2.75 | 0.1018|
|usb_phy | 1.75 | -0.0449 | 2 | 0.1821|
|wb_dma | 3 | -0.0746 | 3.25 | 0.0708|

## Getting Started

### Installation

The key dependencies that are required by EDA-schema are the following

 - [Python 3.10](https://www.python.org/) or later
 - [PDM](https://pdm-project.org/)

Clone the [repository](https://github.com/drexel-ice/eda-schema) then prepare its environment:

```bash
$ git clone git@github.com:drexel-ice/eda-schema.git
$ cd eda-schema
$ pdm install
```

### Get Open Dataset

The open dataset is available [publicly](https://drive.google.com/drive/folders/1B3rBvbnviBrKw1aLRpv7e1pEXSCy_vLQ?usp=sharing).

Following are the details on the post routed designs in the open dataset
- Overall circuits in dataset: 16 * 2 = 32
- Number of gates in dataset: 148,687 (excluding fillers, tap cells)
- Number of nets in dataset: 148,337
- Number of timing paths in dataset: 125,256
- Total dataset size: 23GB​

To use the dataset, download the data dump and use the following commands.
```python
from eda_schema.dataset import Dataset
from eda_schema.db import SQLitePickleDB

DATASET_DIR = "../dataset/dataset_openroad_sky130hd_iwls05_v1.1_final"
dataset = Dataset(SQLitePickleDB(DATASET_DIR<path_to_the_data_dump>
```

### Run Jupyter Lab

```bash
$ pdm jupyter
```

### Generate docs

To generate the documentation run:
```bash
$ pdm docs
```

## Cite this work

- P. Shrestha, A. Aversa, S. Phatharodom, and I. Savidis, "**EDA-schema: A graph datamodel schema and open dataset for digital design automation**", Proceedings of the ACM Great Lakes Symposium on VLSI (GLSVLSI), pp. 69–77, Jun. 2024.

## Contact

- For any questions, support, or if you have issues accessing the dataset, please send us an email at [ps937@drexel.edu](mailto:ps937@drexel.edu), [is338@drexel.edu](mailto:is338@drexel.edu).
- If you encounter any bugs or have any issues, please feel free to [open an issue](https://github.com/drexel-ice/EDA-schema/issues). We appreciate your feedback and will work to address any problems as quickly as possible.
