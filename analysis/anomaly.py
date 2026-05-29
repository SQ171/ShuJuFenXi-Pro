"""Pipeline S7: 异常检测 — σ离群 + 特征偏离 + 趋势偏离"""

import numpy as np
import pandas as pd
from analysis.pipeline import AnalysisContext
from core.constants import (
    COL_STEP_ID, COL_NOMINAL_THROTTLE, COL_CYCLE_NUM,
    COL_SOURCE_FILE, COL_IS_STABILIZING, COL_SYS_EFF, COL_THRUST,
    COL_ELEC_POWER,
)
from config import ALL_METRICS, DEGRADATION_SIGMA


def detect_anomalies(ctx: AnalysisContext) -> AnalysisContext:
    df = ctx.unified_df
    if df is None or df.empty:
        return ctx

    df = df.copy()
    df["is_outlier"] = False
    df["outlier_reason"] = ""

    for (source_file, cycle_num, step_id), group in df.groupby(
        [COL_SOURCE_FILE, COL_CYCLE_NUM, COL_STEP_ID], sort=True
    ):
        stable_mask = ~group[COL_IS_STABILIZING]
        stable = group[stable_mask]
        if len(stable) < 10:
            continue

        indices = group.index[stable_mask]

        for metric in [m for m in ALL_METRICS if m.degradation_sensitive]:
            col = metric.col_name
            if col not in stable.columns:
                continue
            values = stable[col].dropna()
            if len(values) < 10:
                continue

            mean = np.mean(values)
            std = np.std(values)
            if std == 0:
                continue

            lower = mean - DEGRADATION_SIGMA * std
            upper = mean + DEGRADATION_SIGMA * std

            outlier_idx = values.index[(values < lower) | (values > upper)]
            for idx in outlier_idx:
                actual_idx = indices[stable.index.get_loc(idx)]
                if not df.at[actual_idx, "is_outlier"]:
                    df.at[actual_idx, "is_outlier"] = True
                    df.at[actual_idx, "outlier_reason"] = f"{metric.display_name}偏离{mean:.2f}±{DEGRADATION_SIGMA}σ"

    ctx.anomaly_flags = df[["is_outlier", "outlier_reason"]]
    ctx.unified_df = df
    return ctx
