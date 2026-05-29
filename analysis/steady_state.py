"""Pipeline S4: 稳态统计 — 按台阶计算 mean/std/cv/min/max/percentile"""

import numpy as np
import pandas as pd
from analysis.pipeline import AnalysisContext
from core.constants import (
    COL_STEP_ID, COL_NOMINAL_THROTTLE, COL_CYCLE_NUM,
    COL_SOURCE_FILE, COL_IS_STABILIZING, COL_ELEC_POWER,
)
from config import ALL_METRICS


def compute_steady_state(ctx: AnalysisContext) -> AnalysisContext:
    df = ctx.unified_df
    if df is None or df.empty:
        return ctx

    rows = []
    for (source_file, cycle_num, step_id), group in df.groupby(
        [COL_SOURCE_FILE, COL_CYCLE_NUM, COL_STEP_ID], sort=True
    ):
        if group.empty or group[COL_NOMINAL_THROTTLE].isna().all():
            continue

        nominal_throttle = group[COL_NOMINAL_THROTTLE].mode()
        if len(nominal_throttle) == 0:
            continue
        nominal_throttle = float(nominal_throttle.iloc[0])

        stable = group[~group[COL_IS_STABILIZING]]
        if len(stable) < 5:
            continue

        row = {
            "source_file": source_file,
            "cycle_num": int(cycle_num),
            "step_id": int(step_id),
            "nominal_throttle": nominal_throttle,
            "sample_count": len(group),
            "stabilization_count": len(group) - len(stable),
        }

        for metric in ALL_METRICS:
            col = metric.col_name
            if col not in stable.columns:
                continue
            values = stable[col].dropna().values
            if len(values) < 5:
                continue

            # 力效过滤：排除功率<1W的数据
            if metric.key == "force_eff" and COL_ELEC_POWER in stable.columns:
                mask = stable[COL_ELEC_POWER] >= 1.0
                eff_values = stable.loc[mask, col].dropna()
                if len(eff_values) > 0:
                    values = eff_values.values
                else:
                    continue

            abs_values = np.abs(values)
            row[f"{metric.key}_mean"] = float(np.mean(abs_values))
            row[f"{metric.key}_std"] = float(np.std(abs_values))
            row[f"{metric.key}_cv"] = float(np.std(abs_values) / np.mean(abs_values) * 100) if np.mean(abs_values) != 0 else 0.0
            row[f"{metric.key}_min"] = float(np.min(abs_values))
            row[f"{metric.key}_max"] = float(np.max(abs_values))
            row[f"{metric.key}_p5"] = float(np.percentile(abs_values, 5))
            row[f"{metric.key}_p95"] = float(np.percentile(abs_values, 95))
            row[f"{metric.key}_rms"] = float(np.sqrt(np.mean(abs_values ** 2)))

        rows.append(row)

    ctx.step_summary = pd.DataFrame(rows)
    return ctx
