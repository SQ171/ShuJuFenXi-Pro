"""Pipeline S3: 运行时间计算"""

import numpy as np
from analysis.pipeline import AnalysisContext
from core.models import RuntimeInfo
from core.constants import (
    COL_CUMULATIVE_RUNTIME, COL_FRAME_TIME,
    COL_SOURCE_FILE, COL_CYCLE_NUM, COL_RUNTIME_HOURS,
)


def compute_runtime(ctx: AnalysisContext) -> AnalysisContext:
    df = ctx.unified_df
    if df is None or df.empty:
        return ctx

    df = df.sort_values([COL_SOURCE_FILE, COL_FRAME_TIME]).reset_index(drop=True)

    per_file_runtime = {}
    all_per_cycle_durations = []

    for run in ctx.test_runs:
        per_file_runtime[run.filename] = run.duration_seconds

    cumulative = np.zeros(len(df))
    file_groups = df.groupby(COL_SOURCE_FILE)
    running_total = 0.0

    for filename, group in file_groups:
        indices = group.index.values
        times = group[COL_FRAME_TIME].values

        offsets = (times - times[0]) / np.timedelta64(1, 's')
        cumulative[indices] = running_total + offsets
        running_total += per_file_runtime.get(filename, 0.0)

        if COL_CYCLE_NUM in group.columns:
            for _, cycle_group in group.groupby(COL_CYCLE_NUM):
                ct = cycle_group[COL_FRAME_TIME].values
                if len(ct) > 1:
                    all_per_cycle_durations.append(
                        (ct[-1] - ct[0]) / np.timedelta64(1, 's'))

    df[COL_CUMULATIVE_RUNTIME] = cumulative
    df[COL_RUNTIME_HOURS] = cumulative / 3600.0

    ctx.unified_df = df
    ctx.runtime_info = RuntimeInfo(
        per_file_runtime=per_file_runtime,
        total_runtime_seconds=sum(per_file_runtime.values()),
        per_cycle_durations=all_per_cycle_durations,
        cumulative_runtime_column=COL_CUMULATIVE_RUNTIME,
    )
    return ctx
