## Open Dataset

EDA-Schema-V2 includes a large scale open dataset of digital physical designs generated using fully open source tools, open benchmark circuits, and publicly available process design kits (PDKs). The dataset is designed to support reproducible machine learning research in digital physical design by providing multimodal circuit representations, stage resolved design snapshots, and standardized benchmark tasks.

The dataset is generated from four primary components:

1) **Benchmark Circuits**
   Selected circuits from the [IWLS'05 benchmark suite](https://github.com/ieee-ceda-datc/RDF-2020/tree/master/benchmarks/iwls05_opencores), spanning diverse functional blocks and circuit complexities.

2) **Process Design Kits (PDKs)**
   Four open source technology nodes are used:

   - [SkyWater 130 nm](https://skywater-pdk.readthedocs.io/en/main/)
   - Nangate 45 nm
   - IHP SG13G2 130 nm
   - ASAP 7 nm

3) **Physical Design Toolchain**
   [OpenROAD](https://theopenroadproject.org/) is used to generate complete RTL to GDSII physical implementations, including synthesis, floorplanning, placement, clock tree synthesis, routing, parasitic extraction, timing analysis, and PDN analysis.

4) **Design Constraints and Parameter Sweeps**
   Physical designs are generated under varying design constraints and implementation parameters, including:

   - Target clock period
   - Clock uncertainty
   - Clock latency
   - Clock transition constraints
   - Input delay
   - Output delay
   - Core utilization
   - Aspect ratio

Rather than using fixed design settings, EDA-Schema-V2 performs systematic sweeps over:

- **Clock period**
- **Core utilization**
- **Aspect ratio**

This produces both timing clean and timing violating implementations across multiple operating points.

### Barely Pass and Barely Fail Operating Points

For each benchmark circuit and PDK, two representative operating points are identified:

  - **Barely Pass (BP)**
  Slight positive slack
  Slack to Clock Period Ratio (SCPR) ∈ (0%, +10%)

  - **Barely Fail (BF)**
  Slight negative slack
  SCPR ∈ (−10%, 0%)

These operating points provide controlled timing variation for learning timing related prediction tasks.


### Initial Barely Pass and Barely Fail Operating Points

Initial Barely Pass and Barely Fail operating points are identified for each benchmark circuit across all four PDKs:


#### Nangate 45 nm

| Circuit | Barely Pass TCP | Barely Pass WS | Barely Pass SCPR | Barely Fail TCP | Barely Fail WS | Barely Fail SCPR |
|---|---:|---:|---:|---:|---:|---:|
| ac97_ctrl | 0.60 | 0.0078 | 1.30% | 0.50 | -0.0425 | -8.50% |
| aes_core | 1.50 | 0.1158 | 7.72% | 1.25 | -0.0412 | -3.30% |
| des3_area | 2.50 | 0.0006 | 0.02% | 2.25 | -0.0411 | -1.83% |
| ethernet | 1.65 | 0.0204 | 1.24% | 1.50 | -0.0220 | -1.47% |
| i2c | 0.65 | 0.0103 | 1.58% | 0.55 | -0.0154 | -2.79% |
| jpeg | 1.80 | 0.0483 | 2.68% | 1.60 | -0.0117 | -0.73% |
| mem_ctrl | 1.75 | 0.0202 | 1.15% | 1.25 | -0.0558 | -4.46% |
| pci | 1.00 | 0.0398 | 3.98% | 0.75 | -0.0328 | -4.37% |
| sasc | 0.60 | 0.0252 | 4.19% | 0.50 | -0.0392 | -7.84% |
| simple_spi | 0.55 | 0.0258 | 4.69% | 0.45 | -0.0421 | -9.35% |
| spi | 1.50 | 0.0595 | 3.96% | 1.25 | -0.0142 | -1.14% |
| ss_pcm | 0.38 | 0.0111 | 2.92% | 0.325 | -0.0133 | -4.08% |
| systemcaes | 1.75 | 0.0809 | 4.62% | 1.50 | -0.0064 | -0.43% |
| systemcdes | 1.45 | 0.1219 | 8.41% | 1.25 | -0.0143 | -1.15% |
| tv80 | 2.25 | 0.0940 | 4.18% | 1.90 | -0.0028 | -0.15% |
| usb_funct | 1.00 | 0.0035 | 0.35% | 0.80 | -0.0068 | -0.85% |
| usb_phy | 0.45 | 0.0068 | 1.51% | 0.35 | -0.0193 | -5.52% |
| wb_dma | 1.25 | 0.0230 | 1.84% | 0.90 | -0.0683 | -7.59% |

#### ASAP 7 nm

| Circuit | Barely Pass TCP | Barely Pass WS | Barely Pass SCPR | Barely Fail TCP | Barely Fail WS | Barely Fail SCPR |
|---|---:|---:|---:|---:|---:|---:|
| ac97_ctrl | 0.375 | 0.0030 | 0.80% | 0.350 | -0.0066 | -1.90% |
| aes_core | 0.750 | 0.0074 | 0.99% | 0.725 | -0.0105 | -1.45% |
| des3_area | 1.225 | 0.0014 | 0.11% | 1.200 | -0.0042 | -0.35% |
| ethernet | 0.750 | 0.0166 | 2.22% | 0.725 | -0.0404 | -5.57% |
| i2c | 0.375 | 0.0042 | 1.13% | 0.350 | -0.0079 | -2.27% |
| jpeg | 1.125 | 0.0343 | 3.05% | 1.100 | -0.0234 | -2.13% |
| mem_ctrl | 0.875 | 0.0006 | 0.07% | 0.850 | -0.0043 | -0.51% |
| pci | 0.825 | 0.0378 | 4.58% | 0.810 | -0.0257 | -3.17% |
| sasc | 0.400 | 0.0177 | 4.43% | 0.375 | -0.0031 | -0.82% |
| simple_spi | 0.325 | 0.0039 | 1.20% | 0.300 | -0.0052 | -1.73% |
| spi | 0.775 | 0.0047 | 0.61% | 0.750 | -0.0012 | -0.16% |
| ss_pcm | 0.275 | 0.0044 | 1.58% | 0.250 | -0.0110 | -4.40% |
| systemcaes | 0.850 | 0.0059 | 0.70% | 0.825 | -0.0031 | -0.37% |
| systemcdes | 0.750 | 0.0066 | 0.88% | 0.725 | -0.0062 | -0.86% |
| tv80 | 1.200 | 0.0058 | 0.48% | 1.175 | -0.0217 | -1.85% |
| usb_funct | 0.425 | 0.0041 | 0.97% | 0.400 | -0.0010 | -0.25% |
| usb_phy | 0.300 | 0.0040 | 1.32% | 0.275 | -0.0066 | -2.41% |
| wb_dma | 0.700 | 0.0063 | 0.90% | 0.675 | -0.0003 | -0.04% |

#### SkyWater 130 nm

... same format ...

#### IHP SG13G2 130 nm

... same format ...
|wb_dma | 3 | -0.0746 | 3.25 | 0.0708|


### Dataset Scale

The released dataset contains approximately:

- **7,800 design instances**
- **18 benchmark circuits**
- **4 open source PDKs**
- **~275 million gates**
- **~75 million nets**
- **>36 million extracted timing paths**


The open dataset is available [publicly](https://drive.google.com/drive/folders/1B3rBvbnviBrKw1aLRpv7e1pEXSCy_vLQ?usp=sharing).
