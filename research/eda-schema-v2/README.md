## Research/EDA-Schema v2

This directory hosts cleaned-up research artifacts for EDA schema V2: analysis scripts, datasets, and plots that reproduce the paper’s results when pointed at the dataset specified by `EDA_SCHEMA_V2_DATASET`. The artifacts reflect the same analyses and plots described in:

```bibtex
@inproceedings{shrestha2026edaschema,
  title={EDA-Schema-V2: Multimodal Schema, Open Datasets, and Benchmarks for Machine Learning in Digital Physical Design},
  author={Shrestha, P. and Aversa, A. and Savidis, I.},
}
```

### Key subdirectories

- `baseline_analysis/` – baseline analysis scripts (`run.sh`, `compute_baseline_vs_actual.py`, `compute_error_metrics.py`, `plot.py`) that recompute per-flow metrics and render the final grid plots for each PDK.
- `notebooks/` – Jupyter notebooks that recreate the published analyses, including per-PDK evolution, QoR histograms, timing summaries, and sensitivity studies.
- `results/` – generated CSV summaries, grid plots, and other artifacts (baseline grids, correlation plots, timing pathway compositions) produced by the pipeline.


### Running experiments

1. Activate dependencies (e.g., `source venv/bin/activate`).
2. Set `EDA_SCHEMA_V2_DATASET` before running a script; this is consumed by `compute_baseline_vs_actual.py`.
3. Run `research/eda-schema-v2/baseline_analysis/run.sh` to produce curated CSV outputs and grid PNGs inside `research/eda-schema-v2/results/`.
4. Use the notebooks in `baseline_analysis/notebooks/` to recreate the published plots and investigations (timing evolution, QoR histograms, sensitivity studies, etc.).
