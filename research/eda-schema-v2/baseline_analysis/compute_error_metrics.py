from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

RESULTS_DIR = Path("research/eda-schema-v2/baseline_analysis/results")
OUT_CSV = "baseline_table.csv"

TARGET_STAGE = "detailed_route"

PDK_ORDER = ["NG45", "SKY130", "IHP130", "ASAP7"]

STAGE_ORDER = [
    "floorplan",
    "global_place",
    "detailed_place",
    "cts",
    "global_route",
]

TRANSITION_LABELS = {
    "floorplan": "floorplan to detailed route",
    "global_place": "global place to detailed route",
    "detailed_place": "detailed place to detailed route",
    "cts": "CTS to detailed route",
    "global_route": "global route to detailed route",
}

PROBLEM_LABELS = {
    "total_area_prediction": "Total Area (μm²)",
    "total_power_prediction": "Total Power (μW)",
    "total_wirelength_prediction": "Total Wirelength (μm)",
    "interconnect_length_prediction": "Interconnect Wirelength (μm)",
    "worst_arrival_time_prediction": "Worst Arrival Time (ns)",
    "worst_slack_prediction": "Worst Slack (ns)",
    "total_negative_slack_prediction": "Total Negative Slack (ns)",
    "timing_path_arrival_time_prediction": "Timing Path Arrival Time (ns)",
    "timing_path_slack_prediction": "Timing Path Slack (ns)",
    "net_arc_delay_prediction": "Net Arc Delay (ns)",
    "cell_arc_delay_prediction": "Cell Arc Delay (ns)",
    "cell_arc_slew_prediction": "Cell Arc Slew (ns)",
}

# Mapping back from human label to problem key
METRIC_TO_PROBLEM = {v: k for k, v in PROBLEM_LABELS.items()}

# ✅ Problem-specific metrics (matches your table)
PROBLEM_METRICS = {
    "total_area_prediction": ["MAE", "MAPE", "R2"],
    "total_power_prediction": ["MAE", "MAPE", "R2"],
    "total_wirelength_prediction": ["MAE", "MAPE", "R2"],
    "interconnect_length_prediction": [
        "MAE",
        "MAPE",
        "R2",
        "MAE_P95",
        "MAPE_P95",
        "MAE_TOP5",
        "MAPE_TOP5",
    ],
    "worst_arrival_time_prediction": ["MAE", "MAPE"],
    "worst_slack_prediction": ["MAE", "MPE", "MNE", "TPR", "TNR"],
    "total_negative_slack_prediction": ["MAE", "MPE", "MNE"],
    "timing_path_arrival_time_prediction": [
        "MAE",
        "MAPE",
        "MAE_P95",
        "MAPE_P95",
        "MAE_TOP5",
        "MAPE_TOP5",
    ],
    "timing_path_slack_prediction": ["MAE", "MPE", "MNE", "TPR", "TNR"],
    "net_arc_delay_prediction": ["MAE", "MAPE", "R2"],
    "cell_arc_delay_prediction": ["MAE", "MAPE", "R2"],
    "cell_arc_slew_prediction": ["MAE", "MAPE", "R2"],
}

ROUND_RULES = {
    "timing_path_arrival_time_prediction": {"MAE", "MAE_P95", "MAE_TOP5"},
    "timing_path_slack_prediction": {"MAE", "MPE", "MNE"},
    "net_arc_delay_prediction": {"MAE"},
    "cell_arc_delay_prediction": {"MAE"},
    "cell_arc_slew_prediction": {"MAE"},
}


def _maybe_round(problem: str, stat: str, value: float) -> float:
    if problem in ROUND_RULES and stat in ROUND_RULES[problem] and np.isfinite(value):
        return round(value, 4)
    return value


NETLIST_LEVEL_PROBLEMS = {
    "total_area_prediction",
    "total_power_prediction",
    "total_wirelength_prediction",
    "worst_arrival_time_prediction",
    "worst_slack_prediction",
    "total_negative_slack_prediction",
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


def safe_mape(y_true, y_pred, eps=1e-12):
    denom = np.maximum(np.abs(y_true), eps)
    return np.mean(np.abs((y_true - y_pred) / denom))


def _parse_stage_dir(stage_dir: Path) -> tuple[str, str, str] | None:
    import re

    pattern = re.compile(
        r"(?P<problem>.+)_(?P<pdk>NG45|SKY130|IHP130|ASAP7)_(?P<stage>floorplan|global_place|detailed_place|cts|global_route)"
    )
    match = pattern.fullmatch(stage_dir.name)
    if not match:
        return None
    return match.group("problem"), match.group("pdk"), match.group("stage")


def _collect_stage_xy(
    stage_dir: Path, problem: str
) -> tuple[np.ndarray, np.ndarray] | None:
    if not stage_dir.exists():
        return None

    if problem in NETLIST_LEVEL_PROBLEMS:
        csv_path = stage_dir / "all_circuits.csv"
        if not csv_path.exists():
            return None
        df = pd.read_csv(csv_path, usecols=["baseline", "target"])
        return (
            df["baseline"].to_numpy(dtype=np.float32),
            df["target"].to_numpy(dtype=np.float32),
        )

    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    for csv_path in list(stage_dir.glob("*.csv")):
        if csv_path.name == "all_circuits.csv":
            continue
        df = pd.read_csv(csv_path, usecols=["baseline", "target"])
        baseline = pd.to_numeric(df["baseline"], errors="coerce")
        target = pd.to_numeric(df["target"], errors="coerce")
        mask = np.isfinite(baseline) & np.isfinite(target)
        if mask.any():
            xs.append(baseline[mask].to_numpy(dtype=np.float32))
            ys.append(target[mask].to_numpy(dtype=np.float32))
    if not xs:
        return None
    return np.concatenate(xs), np.concatenate(ys)


def _compute_error_metrics(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    if len(x) < 2:
        return {}

    err = x - y
    abs_err = np.abs(err)
    denom = np.maximum(np.abs(y), 1e-12)

    stats = {
        "MAE": np.mean(abs_err),
        "MAPE": safe_mape(y, x),
        "R2": r2_score(y, x),
        "MAE_P95": np.percentile(abs_err, 95),
        "MAPE_P95": np.percentile(abs_err / denom, 95),
    }

    threshold = np.percentile(y, 95)
    mask_top5 = y >= threshold
    stats["MAE_TOP5"] = np.mean(abs_err[mask_top5]) if np.any(mask_top5) else np.nan
    stats["MAPE_TOP5"] = (
        safe_mape(y[mask_top5], x[mask_top5]) if np.any(mask_top5) else np.nan
    )

    pos = err[err > 0]
    neg = err[err < 0]
    stats["MPE"] = np.mean(pos) if len(pos) else np.nan
    stats["MNE"] = np.mean(np.abs(neg)) if len(neg) else np.nan

    true_v = y < 0
    pred_v = x < 0

    TP = np.sum(true_v & pred_v)
    TN = np.sum(~true_v & ~pred_v)
    FP = np.sum(~true_v & pred_v)
    FN = np.sum(true_v & ~pred_v)

    stats["TPR"] = TP / (TP + FN) if (TP + FN) else np.nan
    stats["TNR"] = TN / (TN + FP) if (TN + FP) else np.nan

    return stats


def _process_stage(stage_dir: Path, problem: str) -> dict[str, float]:
    print(f"Processing {problem} {pdk} {stage}")
    xy = _collect_stage_xy(stage_dir, problem)
    if xy is None:
        return None
    x, y = xy
    print("x.shape, y.shape", x.shape, y.shape)

    print("Computing error metrics...")
    stats = _compute_error_metrics(x, y)
    print(stats)
    return stats


records = []

for stage_dir in RESULTS_DIR.iterdir():
    if not stage_dir.is_dir():
        continue
    parsed = _parse_stage_dir(stage_dir)
    if parsed is None:
        continue
    problem, pdk, stage = parsed
    if stage not in STAGE_ORDER or problem not in PROBLEM_METRICS:
        continue

    stats = _process_stage(stage_dir, problem)
    if stats is None:
        continue

    allowed_stats = PROBLEM_METRICS.get(problem, [])
    for stat in allowed_stats:
        value = stats.get(stat, np.nan)
        # value = _maybe_round(problem, stat, value)
        records.append(
            {
                "Metric": PROBLEM_LABELS.get(problem, problem),
                "Stat": stat,
                "Transition": TRANSITION_LABELS[stage],
                "PDK": pdk,
                "Value": value,
            }
        )

# Pivot
table = pd.DataFrame(records).pivot_table(
    index=["Metric", "Stat"],
    columns=["Transition", "PDK"],
    values="Value",
    aggfunc="first",
)

# Row ordering (problem-specific)
row_order = []
for problem, stats in PROBLEM_METRICS.items():
    metric_name = PROBLEM_LABELS.get(problem, problem)
    for stat in stats:
        row_order.append((metric_name, stat))

table = table.reindex(
    index=pd.MultiIndex.from_tuples(row_order, names=["Metric", "Stat"])
)

table = table.reindex(
    columns=pd.MultiIndex.from_product(
        [[TRANSITION_LABELS[s] for s in STAGE_ORDER], PDK_ORDER]
    )
)


# Row ordering (problem-specific)


# Formatting
def format_cell(val, stat, metric):
    if pd.isna(val):
        return ""

    problem = METRIC_TO_PROBLEM.get(metric)
    if problem in ROUND_RULES and stat in ROUND_RULES[problem] and np.isfinite(val):
        val = round(val, 4)

    if stat.startswith("MAPE") or stat.startswith("TPR") or stat.startswith("TNR"):
        pct = val * 100
        if pct > 10000:
            return ">10000%"
        return f"{pct:.2f}%"

    if stat == "R2":
        if val < -1:
            return "<-1"
        return f"{val:.3f}"

    if problem in ROUND_RULES and stat in ROUND_RULES[problem] and np.isfinite(val):
        return f"{val:.4f}"
    return f"{val:,.2f}"


table_fmt = table.copy()

for idx in table_fmt.index:
    metric, stat = idx
    table_fmt.loc[idx] = table_fmt.loc[idx].map(lambda v: format_cell(v, stat, metric))

print(table_fmt)

table_fmt.to_csv(f"research/eda-schema-v2/results/{OUT_CSV}")
print(f"Saved: {OUT_CSV}")
