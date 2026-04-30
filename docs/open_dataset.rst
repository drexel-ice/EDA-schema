Open Dataset
============

EDA-Schema-V2 includes a large scale open dataset of digital physical designs
generated using fully open source tools, open benchmark circuits, and publicly
available process design kits (PDKs). The dataset is designed to support
reproducible machine learning research in digital physical design by providing
multimodal circuit representations, stage resolved design snapshots, and
standardized benchmark tasks.

The dataset is generated from four primary components:

1. **Benchmark Circuits**

   Selected circuits from the IWLS'05 benchmark suite, spanning diverse
   functional blocks and circuit complexities.

2. **Process Design Kits (PDKs)**

   Four open source technology nodes are used:

   * Nangate 45 nm
   * SkyWater 130 nm
   * IHP SG13G2 130 nm
   * ASAP 7 nm

3. **Physical Design Toolchain**

   OpenROAD is used to generate complete RTL to GDSII physical
   implementations, including synthesis, floorplanning, placement, clock tree
   synthesis, routing, parasitic extraction, timing analysis, and PDN analysis.

4. **Design Constraints and Parameter Sweeps**

   Physical designs are generated under varying design constraints and
   implementation parameters, including:

   * Target clock period
   * Clock uncertainty
   * Clock latency
   * Clock transition constraints
   * Input delay
   * Output delay
   * Core utilization
   * Aspect ratio

Rather than using fixed design settings, EDA-Schema-V2 performs systematic
sweeps over:

* **Clock period**
* **Core utilization**
* **Aspect ratio**

This produces both timing clean and timing violating implementations across
multiple operating points.

Barely Pass and Barely Fail Operating Points
--------------------------------------------

For each benchmark circuit and PDK, two representative operating points are
identified:

**Barely Pass (BP)**

* Slight positive slack
* Slack to Clock Period Ratio (SCPR) ∈ (0%, +10%)

**Barely Fail (BF)**

* Slight negative slack
* SCPR ∈ (−10%, 0%)

These operating points provide controlled timing variation for learning timing
related prediction tasks.

Initial Barely Pass and Barely Fail Operating Points
----------------------------------------------------

Initial Barely Pass and Barely Fail operating points are identified for each
benchmark circuit across all four PDKs.

Nangate 45 nm
^^^^^^^^^^^^^
.. list-table::
   :header-rows: 1

   * - Circuit
     - Barely Pass TCP
     - Barely Pass WS
     - Barely Pass SCPR
     - Barely Fail TCP
     - Barely Fail WS
     - Barely Fail SCPR
   * - ac97_ctrl
     - 0.60
     - 0.0078
     - 1.30%
     - 0.50
     - -0.0425
     - -8.50%
   * - aes_core
     - 1.50
     - 0.1158
     - 7.72%
     - 1.25
     - -0.0412
     - -3.30%
   * - des3_area
     - 2.50
     - 0.0006
     - 0.02%
     - 2.25
     - -0.0411
     - -1.83%
   * - ethernet
     - 1.65
     - 0.0204
     - 1.24%
     - 1.50
     - -0.0220
     - -1.47%
   * - i2c
     - 0.65
     - 0.0103
     - 1.58%
     - 0.55
     - -0.0154
     - -2.79%
   * - jpeg
     - 1.80
     - 0.0483
     - 2.68%
     - 1.60
     - -0.0117
     - -0.73%
   * - mem_ctrl
     - 1.75
     - 0.0202
     - 1.15%
     - 1.25
     - -0.0558
     - -4.46%
   * - pci
     - 1.00
     - 0.0398
     - 3.98%
     - 0.75
     - -0.0328
     - -4.37%
   * - sasc
     - 0.60
     - 0.0252
     - 4.19%
     - 0.50
     - -0.0392
     - -7.84%
   * - simple_spi
     - 0.55
     - 0.0258
     - 4.69%
     - 0.45
     - -0.0421
     - -9.35%
   * - spi
     - 1.50
     - 0.0595
     - 3.96%
     - 1.25
     - -0.0142
     - -1.14%
   * - ss_pcm
     - 0.38
     - 0.0111
     - 2.92%
     - 0.325
     - -0.0133
     - -4.08%
   * - systemcaes
     - 1.75
     - 0.0809
     - 4.62%
     - 1.50
     - -0.0064
     - -0.43%
   * - systemcdes
     - 1.45
     - 0.1219
     - 8.41%
     - 1.25
     - -0.0143
     - -1.15%
   * - tv80
     - 2.25
     - 0.0940
     - 4.18%
     - 1.90
     - -0.0028
     - -0.15%
   * - usb_funct
     - 1.00
     - 0.0035
     - 0.35%
     - 0.80
     - -0.0068
     - -0.85%
   * - usb_phy
     - 0.45
     - 0.0068
     - 1.51%
     - 0.35
     - -0.0193
     - -5.52%
   * - wb_dma
     - 1.25
     - 0.0230
     - 1.84%
     - 0.90
     - -0.0683
     - -7.59%

SkyWater 130 nm
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Circuit
     - Barely Pass TCP
     - Barely Pass WS
     - Barely Pass SCPR
     - Barely Fail TCP
     - Barely Fail WS
     - Barely Fail SCPR
   * - ac97_ctrl
     - 2.50
     - 0.0233
     - 0.93%
     - 2.25
     - -0.0341
     - -1.52%
   * - aes_core
     - 4.75
     - 0.0723
     - 1.52%
     - 4.50
     - -0.0889
     - -1.98%
   * - des3_area
     - 7.75
     - 0.0138
     - 0.18%
     - 7.50
     - -0.2478
     - -3.30%
   * - ethernet
     - 5.25
     - 0.0856
     - 1.63%
     - 5.00
     - -0.1807
     - -3.61%
   * - i2c
     - 2.75
     - 0.0772
     - 2.81%
     - 2.50
     - -0.1254
     - -5.02%
   * - jpeg
     - 6.00
     - 0.0228
     - 0.38%
     - 5.75
     - -0.3720
     - -6.47%
   * - mem_ctrl
     - 6.25
     - 0.0185
     - 0.30%
     - 6.00
     - -0.1917
     - -3.20%
   * - pci
     - 3.75
     - 0.0861
     - 2.30%
     - 3.50
     - -0.2461
     - -7.03%
   * - sasc
     - 2.25
     - 0.0785
     - 3.49%
     - 2.00
     - -0.0914
     - -4.57%
   * - simple_spi
     - 2.25
     - 0.0828
     - 3.68%
     - 1.90
     - -0.1071
     - -5.64%
   * - spi
     - 4.75
     - 0.1341
     - 2.82%
     - 4.50
     - -0.1181
     - -2.62%
   * - ss_pcm
     - 1.50
     - 0.0594
     - 3.96%
     - 1.35
     - -0.0174
     - -1.29%
   * - systemcaes
     - 5.75
     - 0.1246
     - 2.17%
     - 5.50
     - -0.1404
     - -2.55%
   * - systemcdes
     - 5.00
     - 0.1677
     - 3.35%
     - 4.80
     - -0.0352
     - -0.73%
   * - tv80
     - 8.25
     - 0.0655
     - 0.79%
     - 8.00
     - -0.2718
     - -3.40%
   * - usb_funct
     - 2.75
     - 0.0229
     - 0.83%
     - 2.50
     - -0.0448
     - -1.79%
   * - usb_phy
     - 1.75
     - 0.1531
     - 8.75%
     - 1.50
     - -0.0402
     - -2.68%
   * - wb_dma
     - 4.25
     - 0.0602
     - 1.42%
     - 4.00
     - -0.0645
     - -1.61%

IHP SG13G2 130 nm
^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Circuit
     - Barely Pass TCP
     - Barely Pass WS
     - Barely Pass SCPR
     - Barely Fail TCP
     - Barely Fail WS
     - Barely Fail SCPR
   * - ac97_ctrl
     - 2.35
     - 0.0415
     - 1.77%
     - 2.30
     - -0.0612
     - -2.66%
   * - aes_core
     - 4.25
     - 0.1046
     - 2.46%
     - 4.00
     - -0.3553
     - -8.88%
   * - des3_area
     - 8.50
     - 0.2000
     - 2.35%
     - 8.25
     - -0.0561
     - -0.68%
   * - ethernet
     - 5.50
     - 0.1467
     - 2.67%
     - 5.25
     - -0.1679
     - -3.20%
   * - i2c
     - 2.25
     - 0.0197
     - 0.88%
     - 2.00
     - -0.0857
     - -4.29%
   * - jpeg
     - 9.50
     - 0.3750
     - 3.95%
     - 9.25
     - -0.1166
     - -1.26%
   * - mem_ctrl
     - 5.25
     - 0.2560
     - 4.88%
     - 5.00
     - -0.1356
     - -2.71%
   * - pci
     - 3.50
     - 0.2581
     - 7.37%
     - 3.25
     - -0.0176
     - -0.54%
   * - sasc
     - 2.00
     - 0.0537
     - 2.69%
     - 1.75
     - -0.0443
     - -2.53%
   * - simple_spi
     - 1.75
     - 0.0709
     - 4.05%
     - 1.50
     - -0.0196
     - -1.31%
   * - spi
     - 4.75
     - 0.1467
     - 3.09%
     - 4.50
     - -0.0779
     - -1.73%
   * - ss_pcm
     - 1.40
     - 0.1014
     - 7.24%
     - 1.20
     - -0.0859
     - -7.16%
   * - systemcaes
     - 5.50
     - 0.0415
     - 0.75%
     - 5.25
     - -0.3941
     - -7.51%
   * - systemcdes
     - 4.00
     - 0.2955
     - 7.39%
     - 3.75
     - -0.0634
     - -1.69%
   * - tv80
     - 7.50
     - 0.2298
     - 3.06%
     - 7.25
     - -0.1341
     - -1.85%
   * - usb_funct
     - 3.25
     - 0.1478
     - 4.55%
     - 3.00
     - -0.1618
     - -5.39%
   * - usb_phy
     - 1.40
     - 0.0876
     - 6.26%
     - 1.25
     - -0.0360
     - -2.88%
   * - wb_dma
     - 4.50
     - 0.1333
     - 2.96%
     - 4.25
     - -0.0114
     - -0.27%

ASAP 7 nm
^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Circuit
     - Barely Pass TCP
     - Barely Pass WS
     - Barely Pass SCPR
     - Barely Fail TCP
     - Barely Fail WS
     - Barely Fail SCPR
   * - ac97_ctrl
     - 0.375
     - 0.0030
     - 0.80%
     - 0.350
     - -0.0066
     - -1.90%
   * - aes_core
     - 0.750
     - 0.0074
     - 0.99%
     - 0.725
     - -0.0105
     - -1.45%
   * - des3_area
     - 1.225
     - 0.0014
     - 0.11%
     - 1.200
     - -0.0042
     - -0.35%
   * - ethernet
     - 0.750
     - 0.0166
     - 2.22%
     - 0.725
     - -0.0404
     - -5.57%
   * - i2c
     - 0.375
     - 0.0042
     - 1.13%
     - 0.350
     - -0.0079
     - -2.27%
   * - jpeg
     - 1.125
     - 0.0343
     - 3.05%
     - 1.100
     - -0.0234
     - -2.13%
   * - mem_ctrl
     - 0.875
     - 0.0006
     - 0.07%
     - 0.850
     - -0.0043
     - -0.51%
   * - pci
     - 0.825
     - 0.0378
     - 4.58%
     - 0.810
     - -0.0257
     - -3.17%
   * - sasc
     - 0.400
     - 0.0177
     - 4.43%
     - 0.375
     - -0.0031
     - -0.82%
   * - simple_spi
     - 0.325
     - 0.0039
     - 1.20%
     - 0.300
     - -0.0052
     - -1.73%
   * - spi
     - 0.775
     - 0.0047
     - 0.61%
     - 0.750
     - -0.0012
     - -0.16%
   * - ss_pcm
     - 0.275
     - 0.0044
     - 1.58%
     - 0.250
     - -0.0110
     - -4.40%
   * - systemcaes
     - 0.850
     - 0.0059
     - 0.70%
     - 0.825
     - -0.0031
     - -0.37%
   * - systemcdes
     - 0.750
     - 0.0066
     - 0.88%
     - 0.725
     - -0.0062
     - -0.86%
   * - tv80
     - 1.200
     - 0.0058
     - 0.48%
     - 1.175
     - -0.0217
     - -1.85%
   * - usb_funct
     - 0.425
     - 0.0041
     - 0.97%
     - 0.400
     - -0.0010
     - -0.25%
   * - usb_phy
     - 0.300
     - 0.0040
     - 1.32%
     - 0.275
     - -0.0066
     - -2.41%
   * - wb_dma
     - 0.700
     - 0.0063
     - 0.90%
     - 0.675
     - -0.0003
     - -0.04%

Dataset Scale
-------------

The released dataset contains approximately:

* **7,800 design instances**
* **18 benchmark circuits**
* **4 open source PDKs**
* **~275 million gates**
* **~75 million nets**
* **>36 million extracted timing paths**

Public Availability
-------------------

The open dataset is available `publicly <https://drive.google.com/drive/folders/1B3rBvbnviBrKw1aLRpv7e1pEXSCy_vLQ?usp=sharing>`_.
