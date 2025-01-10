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

The open dataset is available [publicly](https://drexel0.sharepoint.com/:f:/r/sites/ICETeam/Shared%20Documents/Digital%20Design%20Group/ML-AI%20CAD%20project/Datasets/EDA-schema-open-dataset?csf=1&web=1&e=hvFzIV) as a zip file of mongoDB data dump.

Following are the details on the open dataset

### Full dataset
- consists of all the generated circuits
- Overall circuits in dataset: 48 * 20 = 960​
- Number of gates in dataset: 7,468,228​
- Number of nets in dataset: 7,726,920​
- Number of timing paths in dataset: 1,561,975​
- Total dataset size: 82.836G​

### Minimal dataset
- consists of a small subset generated circuits
- Target parameters
    - operating frequency: 1 GHz
    - aspect ratio: 0.5
    - utilization: 70%
- Overall circuits in dataset: 20
- Number of gates in dataset: 272,568
- Number of nets in dataset: 227,148
- Number of timing paths in dataset: 121,298
- Total dataset size: 1.194GB
