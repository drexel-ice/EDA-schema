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

The open dataset is available [publicly](https://drive.google.com/drive/folders/1B3rBvbnviBrKw1aLRpv7e1pEXSCy_vLQ?usp=sharing).

Following are the details on the post routed designs in the open dataset
- Overall circuits in dataset: 16 * 2 = 32
- Number of gates in dataset: 757,495
- Number of nets in dataset: 148,337
- Number of timing paths in dataset: 125,256
- Total dataset size: 23GB​
