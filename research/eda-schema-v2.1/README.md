# Research / EDA-Schema v2.1

This work contributes to the versioned physical-design dataset research described in the ICCAD 2026 IEEE CEDA DATC Robust Design Flow paper. Analysis notebooks for the **EDA-Schema v2.1 Barely-Pass / Barely-Fail (BPBF) open dataset**, with per-PDK Parquet schema dumps. The analysis characterizes near-timing-closure flows, examines stage-wise power, performance, and area (PPA), and compares EDA-Schema v2.1 with v2.0.

The notebooks provide reproducible dataset characterization and cross-version comparisons of physical-design behavior. They do not run OpenROAD-ML-Injection experiments.

## 1. Dataset and Provenance

**Open dataset:** [EDA-schema-BPBF-V2.1.0-open-dataset (SharePoint)](https://drexel0-my.sharepoint.com/:f:/r/personal/ps937_drexel_edu/Documents/Drexel-ICE/EDA-schema/EDA-schema-BPBF-V2.1.0-open-dataset?d=w2d013dc366fa4a1c8ad90e3aa97fc80b&csf=1&web=1&e=twAgxN)

Flows were generated with [OpenROAD-flow-scripts (ORFS)](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts) at commit [`c2c8aee`](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/commit/c2c8aee5b7729de05aff5fadaf4c3616f76041ba) (`c2c8aee5b7729de05aff5fadaf4c3616f76041ba`). The v2.0 counterpart corpus used ORFS [`a50fb65`](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/commit/a50fb65).

Each PDK has a **36-flow subset** (18 IWLS designs × 2 configurations), rather than the approximately **1,944-flow per-PDK v2.0 sweep**. Aspect ratio and core utilization are fixed at **1.0** and **40%**, respectively. The two configurations primarily differ in **target clock period (TCP)**.

| Label | v2.1 `flow_id` | v2.0 counterpart | Meaning |
| --- | --- | --- | --- |
| Barely Pass (BP) | `*-000001` | `*-000014` | Retuned near timing closure; final WNS ≥ 0 |
| Barely Fail (BF) | `*-000002` | `*-000023` | Next tighter clock; final WNS < 0 |

**Slack-to-Clock-Period Ratio (SCPR)** is defined as `100 × WNS / TCP` (percent of the target period). The intended near-closure bands are **BP: 0% ≤ SCPR ≤ 10%** and **BF: −10% ≤ SCPR < 0%**. The notebooks verify observed BP/BF classifications using final WNS rather than assuming that labels always match the postprocessed timing values.

The released archive uses this layout:

```text
EDA-schema-BPBF-V2.1.0-open-dataset/
├── nangate45/
├── sky130hd/
├── ihp-sg13g2/
└── asap7/
```

Related v2.0 research is in `research/eda-schema-v2/`.

**Comparison note:** v2.1 regenerates the BP/BF subset on ORFS `c2c8aee` and retunes clock periods near closure. Since TCP often changes relative to v2.0, PPA and timing deltas reflect both software-version and constraint differences, not an isolated ORFS regression.

## 2. Notebooks

| Notebook | PDK folder |
| --- | --- |
| `notebooks/Analysis-NG45.ipynb` | `nangate45` |
| `notebooks/Analysis-SKY130.ipynb` | `sky130hd` |
| `notebooks/Analysis-IHP130.ipynb` | `ihp-sg13g2` |
| `notebooks/Analysis-ASAP7.ipynb` | `asap7` |

Each notebook is self-contained for a single PDK. It loads and joins flow, constraint, netlist, cell, area, power, and timing tables; checks BP/BF labels against final TCP, WNS, and SCPR; compares final-stage PPA; plots stage-wise mean metrics across 18 designs; and compares paired v2.0 and v2.1 BP/BF runs using bars, improvement/degradation plots, and mean/median delta heatmaps. Figures and CSV summaries are saved to `results/`.

**Interpretation notes:** Lower area, power, and wirelength are better; higher WNS and TNS are better. Prefer absolute WNS/TNS deltas over percentages near zero. Floorplan HPWL is unavailable in these dumps, so stage-wise wirelength plots start at global placement.

**Timing consistency:** Timing is derived from postprocessed `*_timing_max.json`, not directly from `6_finish.rpt`. Match Liberty, corner, and SPEF settings to the original ORFS flow. For ASAP7, convert v2.1 TCP from picoseconds to nanoseconds (`/1000`) before comparing to v2.0, and use the **TT RVT** Liberty configuration (`CORNER=TC`); an earlier FF default incorrectly made BF cases appear timing-clean.

## 3. Per-PDK Observations (Pooled v2.0 → v2.1)

| PDK | Median TCP change | Observed PPA/timing trend | Interpretation |
| --- | --- | --- | --- |
| **NG45** | ~22% tighter | Small area and wirelength improvements; power ~6.5% higher | BP remains clean; BF remains violating |
| **SKY130** | ~0% | Power and wirelength improve; WNS slightly improves | Closest to a matched cross-version rerun; labels unchanged |
| **IHP130** | ~29% tighter | Large area decrease with large power increase | Different operating point; not an apples-to-apples ORFS regression |
| **ASAP7** | ~8% tighter, after unit conversion | Area and wirelength improve; power increases | BP clean and BF violating for all 18 designs in the current dump |

These are descriptive comparisons of the available paired configurations. In particular, changes in timing targets must be considered before attributing PPA changes to the ORFS update.

## 4. Reproducing the Analysis

Activate the environment, change into the notebook directory, and launch a notebook:

```bash
source venv/bin/activate
cd research/eda-schema-v2.1/notebooks
jupyter notebook Analysis-NG45.ipynb
```

Point the notebook to the extracted v2.1 open-dataset folder for the relevant PDK. The v2.0 Parquet dumps are read from either:

- `$EDA_SCHEMA_V2_DATASET/{pdk}`
- `/mnt/swapresearchdata/eda-schema-V2-datasets/{pdk}`

Figures and CSVs are written to `results/`. Example files include:

```text
{PDK}_bpbf_tcp_wns_scpr.png
{PDK}_v20_vs_v21_bars.png
{PDK}_v20_vs_v21_delta_heatmap.png
```

## 5. Citation

If you use the dataset, notebooks, or related EDA-Schema research, please cite the relevant publications:

```bibtex
@article{shrestha2026edaschemav2,
  title={EDA-Schema-V2: A Multimodal Schema, Open Datasets, and Benchmarks for Machine Learning in Digital Physical Design},
  author={Shrestha, P. and Aversa, A. and Savidis, I.},
  journal={arXiv preprint arXiv:2605.06952},
  pages={1--39},
  year={2026},
  month={May}
}

@inproceedings{shrestha2024edaschema,
  title={EDA-schema: A graph datamodel schema and open dataset for digital design automation},
  author={Shrestha, P. and Aversa, A. and Phatharodom, S. and Savidis, I.},
  booktitle={Proceedings of the ACM Great Lakes Symposium on VLSI (GLSVLSI)},
  pages={1--8},
  year={2024},
  month={Jun.}
}

@inproceedings{aversa2026rdf,
  title={Invited: 2026 Extensions of IEEE CEDA DATC's Robust Design Flow and Other Activities},
  author={Aversa, A. and Chinnery, D. and Ghose, A. and Jain, A. and Johnson, A. and Kothari, Y. and Lee, J. and Liu, Y. and Markarian, D. and Oishwee, S. J. and Saiyara, F. A. and Savidis, I. and Shrestha, P. and Sirois, P. and Wang, Z.},
  booktitle={Proceedings of the IEEE/ACM International Conference on Computer-Aided Design (ICCAD)},
  pages={1--9},
  year={2026},
  month={Nov.},
  doi={10.1145/3831252.3848499},
  url={https://vlsicad.ucsd.edu/Publications/Conferences/434/c434.pdf}
}
```