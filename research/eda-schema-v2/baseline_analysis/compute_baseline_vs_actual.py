"""Plot baseline (total_hpwl) vs final wirelength for total_wirelength_prediction."""

import gc
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from typing import List, Optional, Tuple

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from eda_schema.dataset import Dataset
from eda_schema.db import ParquetDB

FINAL_STAGE = "detailed_route"

PROBLEM_DICT = {
    "total_area_prediction": {
        "baseline": "total_area",
        "target": "total_area",
        "entity": "area_metrics",
        "join_columns": ["flow_id"],
    },
    "total_power_prediction": {
        "baseline": "total_power",
        "target": "total_power",
        "entity": "power_metrics",
        "join_columns": ["flow_id"],
    },
    "total_wirelength_prediction": {
        "baseline": "total_hpwl",
        "target": "total_wirelength",
        "entity": "netlists",
        "join_columns": ["flow_id"],
    },
    "interconnect_length_prediction": {
        "baseline": "hpwl",
        "target": "length",
        "entity": "nets",
        "join_columns": ["flow_id", "name"],
    },
    "worst_arrival_time_prediction": {
        "baseline": "worst_arrival_time",
        "target": "worst_arrival_time",
        "entity": "timing_metrics",
        "join_columns": ["flow_id"],
    },
    "worst_slack_prediction": {
        "baseline": "worst_slack",
        "target": "worst_slack",
        "entity": "timing_metrics",
        "join_columns": ["flow_id"],
    },
    "total_negative_slack_prediction": {
        "baseline": "total_negative_slack",
        "target": "total_negative_slack",
        "entity": "timing_metrics",
        "join_columns": ["flow_id"],
    },
    "timing_path_arrival_time_prediction": {
        "baseline": "arrival_time",
        "target": "arrival_time",
        "entity": "timing_paths",
        "join_columns": ["flow_id", "startpoint", "endpoint", "path_type"],
    },
    "timing_path_slack_prediction": {
        "baseline": "slack",
        "target": "slack",
        "entity": "timing_paths",
        "join_columns": ["flow_id", "startpoint", "endpoint", "path_type"],
    },
    "net_arc_delay_prediction": {
        "baseline": "delay",
        "target": "delay",
        "entity": "net_arcs",
        "join_columns": ["flow_id", "startpoint", "endpoint", "path_type", "net_name"],
    },
    "cell_arc_delay_prediction": {
        "baseline": "delay",
        "target": "delay",
        "entity": "cell_arcs",
        "join_columns": ["flow_id", "startpoint", "endpoint", "path_type", "gate_name"],
    },
    "cell_arc_slew_prediction": {
        "baseline": "slew",
        "target": "slew",
        "entity": "cell_arcs",
        "join_columns": ["flow_id", "startpoint", "endpoint", "path_type", "gate_name"],
    },
}

NETLIST_LEVEL_PROBLEMS = [
    "total_area_prediction",
    "total_power_prediction",
    "total_wirelength_prediction",
    "worst_arrival_time_prediction",
    "worst_slack_prediction",
    "total_negative_slack_prediction",
]
TIMING_PATH_LEVEL_PROBLEMS = [
    "timing_path_arrival_time_prediction",
    "timing_path_slack_prediction",
]
ARC_LEVEL_PROBLEMS = [
    "net_arc_delay_prediction",
    "cell_arc_delay_prediction",
    "cell_arc_slew_prediction",
]
INTERCONNECT_LENGTH_LEVEL_PROBLEMS = ["interconnect_length_prediction"]

DATASET_DIR = os.environ.get("EDA_SCHEMA_V2_DATASET")
PDK_DATASETS = {
    "NG45": f"{DATASET_DIR}/nangate45",
    "SKY130": f"{DATASET_DIR}/sky130hd",
    "IHP130": f"{DATASET_DIR}/ihp-sg13g2",
    "ASAP7": f"{DATASET_DIR}/asap7",
}

CIRCUITS = [
    "ac97_ctrl",
    "aes_core",
    "des3_area",
    "i2c",
    "mem_ctrl",
    "pci",
    "sasc",
    "simple_spi",
    "spi",
    "ss_pcm",
    "systemcaes",
    "systemcdes",
    "tv80",
    "usb_funct",
    "usb_phy",
    "wb_dma",
    "ethernet",
    "jpeg",
]


class BaselineAnalyzer:
    def __init__(
        self, problem_dict, pdk_datasets, final_stage, flow_ids: List[str] | None = None
    ):
        self.problem_dict = problem_dict
        self.pdk_datasets = pdk_datasets
        self.final_stage = final_stage
        self.flow_ids = flow_ids

    def _get_db(self, pdk: str):
        print(f"[DB] Initializing DB for PDK={pdk} at {self.pdk_datasets[pdk]}")
        return Dataset(ParquetDB(self.pdk_datasets[pdk])).db

    def load_dataframe(
        self, problem: str, pdk: str, initial_stage: str, flow_id: str | None = None
    ) -> pd.DataFrame:
        print(f"\n[LOAD] problem={problem} | pdk={pdk} | initial_stage={initial_stage}")
        db = self._get_db(pdk)
        config = self.problem_dict[problem]
        target = config["target"]
        baseline = config["baseline"]

        print(
            f"[CONFIG] entity={config['entity']} | join_cols={config['join_columns']}"
        )
        print(f"[CONFIG] baseline={baseline} | target={target}")

        join_cols = config["join_columns"]

        print("[QUERY] Fetching initial stage data...")
        if flow_id is not None:
            initial_df = db.get_table_data(
                config["entity"],
                stage=initial_stage,
                flow_id=flow_id,
                columns=join_cols + [baseline],
            )
        else:
            initial_df = db.get_table_data(
                config["entity"], stage=initial_stage, columns=join_cols + [baseline]
            )
        initial_df = initial_df.rename(columns={baseline: "baseline"})
        print(f"[DATA] initial_df shape={initial_df.shape}")

        print("[QUERY] Fetching final stage data...")
        if flow_id is not None:
            final_df = db.get_table_data(
                config["entity"],
                stage=self.final_stage,
                flow_id=flow_id,
                columns=join_cols + [target],
            )
        else:
            final_df = db.get_table_data(
                config["entity"], stage=self.final_stage, columns=join_cols + [target]
            )
        final_df = final_df.rename(columns={target: "target"})
        print(f"[DATA] final_df shape={final_df.shape}")

        print("[MERGE] Merging initial and final dataframes...")
        merged_df = initial_df.merge(
            final_df,
            on=join_cols,
            how="inner",
        )
        print(f"[DATA] merged_df shape={merged_df.shape}")

        if merged_df.empty:
            print("[WARNING] Merged dataframe is EMPTY")

        nan_count = int(merged_df.isna().any(axis=1).sum())
        print(f"[DATA] dropping {nan_count} rows containing NaN before plot")
        merged_df.dropna(inplace=True)

        return merged_df[["baseline", "target"]]

    def extract_arrays(
        self, problem: str, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        print("\n[EXTRACT] Converting dataframe to numpy arrays...")
        config = self.problem_dict[problem]

        target = config["target"]
        baseline = config["baseline"]

        if target == baseline:
            print("[EXTRACT] baseline == target, applying suffix disambiguation")
            target = f"{target}_final"
            baseline = f"{baseline}_initial"

        print(f"[COLUMNS] using baseline={baseline}, target={target}")

        actual_vals = df[target].to_numpy(dtype=np.float64)
        baseline_vals = df[baseline].to_numpy(dtype=np.float64)

        print(f"[ARRAYS] count={len(actual_vals)}")
        print(
            f"[STATS] actual min/max=({actual_vals.min():.4f}, {actual_vals.max():.4f})"
        )
        print(
            f"[STATS] baseline min/max=({baseline_vals.min():.4f}, {baseline_vals.max():.4f})"
        )

        return actual_vals, baseline_vals

    def _build_plot(
        self,
        problem: str,
        initial_stage: str,
        df: pd.DataFrame,
        output: Path,
    ) -> None:
        print("\n[PLOT] Building scatter plot...")
        fig, ax = plt.subplots(figsize=(10, 10))

        global_min = float(df["baseline"].min())
        global_max = float(df["target"].max())
        print(f"[PLOT] global_min={global_min:.4f}, global_max={global_max:.4f}")

        ax.scatter(df["baseline"], df["target"], alpha=0.4, s=5, rasterized=True)
        ax.plot([global_min, global_max], [global_min, global_max], "r--")

        config = self.problem_dict[problem]

        ax.set_title(
            f"{config['baseline']} prediction vs actual "
            f"({initial_stage} -> {self.final_stage})"
        )
        ax.set_xlabel(f"{initial_stage} {config['baseline']}")
        ax.set_ylabel(f"{self.final_stage} {config['baseline']}")

        ax.set_aspect("equal", "box")
        ax.set_xlim(global_min, global_max)
        ax.set_ylim(global_min, global_max)

        fig.tight_layout()

        print(f"[SAVE] Saving figure to {output}")
        fig.savefig(output)
        plt.close(fig)

    def _save_csv(
        self,
        problem: str,
        df: pd.DataFrame,
        output: Path,
    ) -> None:
        print("\n[CSV] Writing CSV output...")
        df.to_csv(output, index=False)
        print(f"[SAVE] Saving CSV to {output}")
        print(f"[DATA] df shape={df.shape}")

    def analyze(
        self,
        problem: str,
        pdk: str,
        initial_stage: str,
        output: Path,
        circuit: str | None = None,
        circuit_index: int | None = None,
    ) -> None:
        print(
            f"\n========== BASELINE ANALYSIS START (problem={problem}, pdk={pdk}, initial_stage={initial_stage}) =========="
        )
        print(f"\n[OUTPUT] Ensuring directory exists: {output.parent}")
        output.parent.mkdir(parents=True, exist_ok=True)

        if problem in NETLIST_LEVEL_PROBLEMS:
            df = self.load_dataframe(problem, pdk, initial_stage)
            if df.empty:
                print(f"[ABORT] No data for all circuits after merge. Exiting early.")
                return
            self._save_csv(problem, df, output / f"all_circuits.csv")
            self._build_plot(problem, initial_stage, df, output / f"all_circuits.png")
            del df
            gc.collect()

        else:
            if circuit is not None and circuit_index is not None:
                flow_ids = [f"{circuit}-{i:06d}" for i in [circuit_index]]
            else:
                flow_ids = [
                    f"{circuit}-{i:06d}" for circuit in CIRCUITS for i in range(1, 109)
                ]
            for flow_id in flow_ids:
                df = self.load_dataframe(problem, pdk, initial_stage, flow_id=flow_id)
                if df.empty:
                    print(f"[ABORT] No data for {flow_id} after merge. Exiting early.")
                    # continue
                self._save_csv(problem, df, output / f"{flow_id}.csv")
                # self._build_plot(problem, initial_stage, df, output / f"{flow_id}.png")
                del df
                gc.collect()

        print(f"\n[DONE] Outputs written to {output} (+ CSV)")
        print(
            f"========== BASELINE ANALYSIS END (problem={problem}, pdk={pdk}, initial_stage={initial_stage}) ==========\n"
        )


@click.command()
@click.option(
    "--problem",
    default=list(PROBLEM_DICT.keys())[0],
    show_default=True,
    help="Target metric.",
)
@click.option(
    "--initial-stage",
    default="global_place",
    show_default=True,
    help="Stage for place/features (e.g. global_place).",
)
@click.option(
    "--pdk",
    default=list(PDK_DATASETS.keys())[0],
    show_default=True,
    help="PDK technology.",
)
@click.option(
    "--bf-bf-flag",
    is_flag=True,
    help="Use BF-BF flow IDs.",
)
@click.option(
    "--circuit",
    default=None,
    help="Circuit to use for the flow IDs.",
)
@click.option(
    "--circuit-index",
    type=int,
    default=None,
    help="Circuit index to use for the flow IDs (1-108).",
)
def main(
    problem: str,
    pdk: str,
    initial_stage: str,
    bf_bf_flag: bool,
    circuit: str | None = None,
    circuit_index: int | None = None,
) -> None:
    """HPWL vs denormalized actual wirelength baseline grid (matches mlp_v3 evaluate baseline plot)."""
    output = Path(f"baseline_analysis/results")
    output.mkdir(parents=True, exist_ok=True)
    output = Path(f"baseline_analysis/results/{problem}_{pdk}_{initial_stage}")
    output.mkdir(parents=True, exist_ok=True)

    if bf_bf_flag:
        flow_ids = [f"{circuit}-{i:06d}" for circuit in CIRCUITS for i in [14, 23]]
    else:
        flow_ids = None
    baseline_analyzer = BaselineAnalyzer(
        PROBLEM_DICT, PDK_DATASETS, FINAL_STAGE, flow_ids=flow_ids
    )
    baseline_analyzer.analyze(
        problem,
        pdk,
        initial_stage,
        output,
        circuit=circuit,
        circuit_index=circuit_index,
    )


if __name__ == "__main__":
    main()
