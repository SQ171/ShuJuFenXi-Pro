"""Pipeline S8: 多文件同油门对比"""

import numpy as np
import pandas as pd
from analysis.pipeline import AnalysisContext
from config import ALL_METRICS


def compare_runs(ctx: AnalysisContext) -> AnalysisContext:
    ss = ctx.step_summary
    if ss is None or ss.empty:
        return ctx

    rows = []
    for throttle in sorted(ss["nominal_throttle"].dropna().unique()):
        throttle_data = ss[ss["nominal_throttle"] == throttle]
        for metric in ALL_METRICS:
            mean_col = f"{metric.key}_mean"
            if mean_col not in throttle_data.columns:
                continue
            for source_file in throttle_data["source_file"].unique():
                file_data = throttle_data[throttle_data["source_file"] == source_file]
                values = file_data[mean_col].dropna().values
                if len(values) == 0:
                    continue
                rows.append({
                    "nominal_throttle": throttle,
                    "source_file": source_file,
                    "metric": metric.display_name,
                    "dimension": metric.dimension.value,
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "n_cycles": len(values),
                })

    ctx.comparison_table = pd.DataFrame(rows) if rows else pd.DataFrame()
    return ctx
