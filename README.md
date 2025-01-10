# EDA-schema

EDA-schema is a property graph datamodel schema developed to represent digital circuit designs and the associated attributes.
The contributions of this work include:
1. A standardized set of graph structures and feature sets representing a digital circuit and corresponding subcomponents
2. A dataset of physical designs generated from the IWLS'05 benchmark circuit suite utilizing the open-source 130 nm Process Design Kit (PDK) provided by Skywater and the open-source toolset OpenROAD

NOTE: This GitHub repository is still in the development phase. We are actively working on adding new features, fixing bugs, and enhancing the overall functionality. We appreciate your patience and understanding as we work to finalize the project.


## Graph Datamodel Schema

EDA-schema is a property graph data-model schema used to represent digital circuits. Netlists and performance reports are extracted from design tools after each stage of the EDA design flow. These files are utilized to derive structural information and performance metrics for each phase. While post-routing netlists and performance metrics are final and complete, earlier stages still provide incomplete yet useful structural information and estimated performance metrics. The data becomes more complete and accurate as the design flow progresses.

A circuit extracted from the design flow is represented as a graph where nodes are IO pins, gates, and wires, and edges are the connections between them. This primary netlist graph representation is complemented by more granular graph representations, such as a timing path graph and an interconnect graph. Together, these representations complete the schema.

Presented is the entity relationship diagram (ERD) of EDA-schema. The primary graph entities—netlist, clock tree, timing path, and interconnect graphs—are highlighted in gold. Additional tabular entities associated with each graph are shown in silver. For each circuit, data is available for four states: post floorplan, post placement, post CTS, and post routing.


![Alt text](schema.png)

## Open Dataset
A comprehensive dataset for physical design is comprised of four key components:
1) Design circuits: selected [IWLS'05 benchmark circuits](https://github.com/ieee-ceda-datc/RDF-2020/tree/master/benchmarks/iwls05_opencores)
2) Process Development Kit (PDK): [Skywater 130 nm](https://skywater-pdk.readthedocs.io/en/main/)
3) Physical Design Toolset: [OpenROAD](https://theopenroadproject.org/)
4) Design parameters and Constraints:

| Parameters                         | Values or Ranges  | # of Samples |
|------------------------------------|-------------------|--------------|
| Clock periods (ns)                 | {0.5, 1, 2, 5}    | 4            |
| Aspect ratio                       | {0.5, 0.75, 1}    | 3            |
| Max utilization                    | {0.3, 0.5}        | 2            |
| Max skew (ns)                      | {0.01 - 0.2}      | 2            |
| Max fanout                         | {50 - 250}        | 2            |
| Max clock network capacitance (pF) | {0.05 - 0.3}      | 2            |
| Max latency (ns)                   | {0 - 1}           | 2            |
| **Total circuits per design**      |                   | **48**       |


## Getting Started

### Installation

The key dependencies that are required by EDA-schema are the following

- python3.6 or beyond
- pip3
- mongoDB

Clone the [repository](https://github.com/drexel-ice/eda-schema) and use [pip](https://pip.pypa.io/en/stable/) for installation.

```bash
$ git clone git@github.com:drexel-ice/eda-schema.git
$ cd eda-schema
$ pip install -e .
```

### Get Open Dataset

The open dataset is available [publicly](https://drexel0.sharepoint.com/:f:/r/sites/ICETeam/Shared%20Documents/Digital%20Design%20Group/ML-AI%20CAD%20project/Datasets/EDA-schema-open-dataset?csf=1&web=1&e=hvFzIV) as a zip file of mongoDB data dump.

Following are the details on the open dataset

1) Full dataset: consists of all the generated circuits
    - Overall circuits in dataset: 48 * 20 = 960​
    - Number of gates in dataset: 7,468,228​
    - Number of nets in dataset: 7,726,920​
    - Number of timing paths in dataset: 1,561,975​
    - Total dataset size: 82.836G​
2) Minimal dataset: consists of a small subset generated circuits
    - Target parameters
        - operating frequency: 1 GHz
        - aspect ratio: 0.5
        - utilization: 70%
    - Overall circuits in dataset: 20
    - Number of gates in dataset: 272,568
    - Number of nets in dataset: 227,148
    - Number of timing paths in dataset: 121,298
    - Total dataset size: 1.194GB

To use the dataset, first download the zip file of mongoDB data dump, unzip it, and execute the following command.
```bash
$ sudo systemctl stop mongod
$ mongod --dbpath <path_to_the_data_dump>
```

## Cite this work

- P. Shrestha, A. Aversa, S. Phatharodom, and I. Savidis, "**EDA-schema: A graph datamodel schema and open dataset for digital design automation**", Proceedings of the ACM Great Lakes Symposium on VLSI (GLSVLSI), pp. 69–77, Jun. 2024.

## Contact

- For any questions, support, or if you have issues accessing the dataset, please send us an email at [ps937@drexel.edu](mailto:ps937@drexel.edu), [is338@drexel.edu](mailto:is338@drexel.edu).
- If you encounter any bugs or have any issues, please feel free to [open an issue](https://github.com/drexel-ice/EDA-schema/issues). We appreciate your feedback and will work to address any problems as quickly as possible.
