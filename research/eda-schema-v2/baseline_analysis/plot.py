#!/usr/bin/env python3

import argparse
import gc
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS_DIR = Path("research/eda-schema-v2/baseline_analysis/results")

PDK_ORDER = ["NG45", "SKY130", "IHP130", "ASAP7"]

STAGE_ORDER = [
    "floorplan",
    "global_place",
    "detailed_place",
    "cts",
    "global_route",
]

TRANSITION_LABELS = {
    "floorplan": "floorplan →\ndetailed route",
    "global_place": "global_place →\ndetailed route",
    "detailed_place": "detailed_place →\ndetailed route",
    "cts": "cts →\ndetailed route",
    "global_route": "global_route →\ndetailed route",
}

PROBLEM_ORDER = [
    "total_area_prediction",
    "total_power_prediction",
    "total_wirelength_prediction",
    "interconnect_length_prediction",
    "worst_arrival_time_prediction",
    "worst_slack_prediction",
    "total_negative_slack_prediction",
    "timing_path_arrival_time_prediction",
    "timing_path_slack_prediction",
    "net_arc_delay_prediction",
    "cell_arc_delay_prediction",
    "cell_arc_slew_prediction",
]

PROBLEM_LABELS = {
    "total_area_prediction": "Total Area\n(μm²)",
    "total_power_prediction": "Total Power\n(μW)",
    "total_wirelength_prediction": "Total\nWirelength\n(μm)",
    "interconnect_length_prediction": "Interconnect\nWirelength\n(μm)",
    "worst_arrival_time_prediction": "Worst Arrival\nTime (ns)",
    "worst_slack_prediction": "Worst Slack\n(ns)",
    "total_negative_slack_prediction": "Total\nNegative\nSlack (ns)",
    "timing_path_arrival_time_prediction": "Timing Path\nArrival Time\n(ns)",
    "timing_path_slack_prediction": "Timing Path\nSlack (ns)",
    "net_arc_delay_prediction": "Net Arc\nDelay (ns)",
    "cell_arc_delay_prediction": "Cell Arc\nDelay (ns)",
    "cell_arc_slew_prediction": "Cell Arc\nSlew (ns)",
}

NETLIST_LEVEL_PROBLEMS = {
    "total_area_prediction",
    "total_power_prediction",
    "total_wirelength_prediction",
    "worst_arrival_time_prediction",
    "worst_slack_prediction",
    "total_negative_slack_prediction",
}


def load_csv_from_dir(directory, problem):
    """
    - Netlist-level: use all_circuits.csv
    - Others: combine all per-flow CSVs
    """
    if problem in NETLIST_LEVEL_PROBLEMS:
        path = directory / "all_circuits.csv"
        if not path.exists():
            return None
        return pd.read_csv(path, usecols=["baseline", "target"])

    # combine per-flow CSVs
    csv_files = list(directory.glob("*.csv"))
    if not csv_files:
        return None

    xs = []
    ys = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, usecols=["baseline", "target"])
        except Exception:
            continue
        baseline = pd.to_numeric(df["baseline"], errors="coerce")
        target = pd.to_numeric(df["target"], errors="coerce")
        mask = np.isfinite(baseline) & np.isfinite(target)
        if mask.any():
            xs.append(baseline[mask].to_numpy(dtype=np.float64))
            ys.append(target[mask].to_numpy(dtype=np.float64))
        del df, baseline, target
        gc.collect()

    if not xs:
        return None

    return pd.DataFrame(
        {
            "baseline": np.concatenate(xs),
            "target": np.concatenate(ys),
        }
    )


def plot_single(ax, stage_dir, problem):
    df = load_csv_from_dir(stage_dir, problem)

    if df is None or df.empty:
        ax.set_facecolor("lightgray")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal", adjustable="box")
        return

    x = df["baseline"].to_numpy(dtype=np.float64)
    y = df["target"].to_numpy(dtype=np.float64)

    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    if len(x) < 2:
        ax.set_facecolor("lightgray")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal", adjustable="box")
        return

    try:
        a, b = np.polyfit(x, y, 1)

        ax.scatter(
            x,
            y,
            s=8,
            alpha=0.1,
            rasterized=True,
        )

        vmin = min(x.min(), y.min())
        vmax = max(x.max(), y.max())

        pad = 0.03 * (vmax - vmin)
        lo = vmin - pad
        hi = vmax + pad

        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)

        ax.set_aspect("equal", adjustable="box")
        ax.set_anchor("C")

        # y = x
        ax.plot([lo, hi], [lo, hi], color="red", linewidth=1.5)

        # regression
        ax.plot([lo, hi], a * np.array([lo, hi]) + b, color="green", linewidth=1.5)

        ax.text(
            1.03,
            0.92,
            f"y = {a:.2f}x\n   +{b:.2f}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=16,
        )

        ax.tick_params(axis="x", labelsize=16)
        ax.tick_params(axis="y", labelsize=16)

    except Exception:
        ax.set_facecolor("lightgray")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal", adjustable="box")


def plot_pdk(pdk, output_dir):
    n_rows = len(PROBLEM_ORDER)
    n_cols = len(STAGE_ORDER)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(5.0 * n_cols + 2, 2.8 * n_rows),
        squeeze=False,
    )

    for i, problem in enumerate(PROBLEM_ORDER):
        for j, stage in enumerate(STAGE_ORDER):
            print(f"Plotting {pdk} | {problem} | {stage}")

            ax = axes[i, j]
            stage_dir = RESULTS_DIR / f"{problem}_{pdk}_{stage}"

            plot_single(ax, stage_dir, problem)

            if i == 0:
                ax.set_title(
                    TRANSITION_LABELS[stage],
                    fontsize=24,
                    pad=10,
                )

            if j == 0:
                ax.annotate(
                    PROBLEM_LABELS[problem],
                    xy=(-0.65, 0.5),
                    xycoords="axes fraction",
                    ha="right",
                    va="center",
                    fontsize=24,
                )

    plt.tight_layout(pad=3.0)

    output = output_dir / f"{pdk}_baseline_grid.png"

    print(f"saving {output}")
    plt.savefig(
        output,
        dpi=100,
        bbox_inches=None,
    )
    plt.close()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output-dir",
        default="research/eda-schema-v2/results",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdk in PDK_ORDER:
        print(f"\nGenerating plot for {pdk}")
        plot_pdk(pdk, output_dir)


if __name__ == "__main__":
    main()
