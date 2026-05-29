"""Pipeline S7: 异常检测"""

import numpy as np
from analysis.pipeline import AnalysisContext
from core.constants import (
    COL_STEP_ID, COL_NOMINAL_THROTTLE, COL_CYCLE_NUM,
    COL_SOURCE_FILE, COL_IS_STABILIZING,
)
from config import ALL_METRICS


def detect_anomalies(ctx: AnalysisContext) -> AnalysisContext:
    df = ctx.unified_df
    if df is None or df.empty:
        return ctx

    sigma = ctx.sigma
    is_outlier = np.zeros(len(df), dtype=bool)
    outlier_reasons = np.full(len(df), "", dtype=object)

    for (source_file, cycle_num, step_id), group in df.groupby(
        [COL_SOURCE_FILE, COL_CYCLE_NUM, COL_STEP_ID], sort=True
    ):
        stable_mask = ~group[COL_IS_STABILIZING].values
        stable_indices = group.index[stable_mask]
        if len(stable_indices) < 10:
            continue

        for metric in [m for m in ALL_METRICS if m.degradation_sensitive]:
            col = metric.col_name
            if col not in group.columns:
                continue
            values = group.loc[stable_indices, col].dropna()
            if len(values) < 10:
                continue

            mean = values.mean()
            std = values.std()
            if std == 0:
                continue

            lower = mean - sigma * std
            upper = mean + sigma * std

            outlier_mask = (values < lower) | (values > upper)
            if not outlier_mask.any():
                continue

            outlier_positions = values.index[outlier_mask]
            reason = f"{metric.display_name}偏离{mean:.2f}±{sigma}σ"
            for pos in outlier_positions:
                if not is_outlier[pos]:
                    is_outlier[pos] = True
                    outlier_reasons[pos] = reason

    df["is_outlier"] = is_outlier
    df["outlier_reason"] = outlier_reasons
    ctx.anomaly_flags = df[["is_outlier", "outlier_reason"]]
    ctx.unified_df = df
    return ctx
