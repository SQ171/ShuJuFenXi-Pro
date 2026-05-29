"""Pipeline S3: 运行时间计算"""

import numpy as np
import pandas as pd
from analysis.pipeline import AnalysisContext
from core.models import RuntimeInfo
from core.constants import (
    COL_CUMULATIVE_RUNTIME, COL_FRAME_TIME,
    COL_SOURCE_FILE, SAMPLING_RATE_HZ,
)


def compute_runtime(ctx: AnalysisContext) -> AnalysisContext:
    df = ctx.unified_df
    if df is None or df.empty:
        return ctx

    df = df.copy()
    df = df.sort_values([COL_SOURCE_FILE, COL_FRAME_TIME]).reset_index(drop=True)

    per_file_runtime = {}
    all_per_cycle_durations = []

    for run in ctx.test_runs:
        per_file_runtime[run.filename] = run.duration_seconds

    # 计算跨文件累计运行时间
    cumulative = np.zeros(len(df))
    file_groups = df.groupby(COL_SOURCE_FILE)
    running_total = 0.0

    for filename, group in file_groups:
        indices = group.index
        times = group[COL_FRAME_TIME].values

        # 每个文件内部的时间偏移（从该文件第一行开始）
        file_start = times[0]
        for j, idx in enumerate(indices):
            offset = (times[j] - file_start) / np.timedelta64(1, 's')
            cumulative[idx] = running_total + offset

        running_total += per_file_runtime.get(filename, 0.0)

        # 计算每个文件内部每循环的持续时间
        from core.constants import COL_CYCLE_NUM
        if COL_CYCLE_NUM in group.columns:
            cycle_groups = group.groupby(COL_CYCLE_NUM)
            for cycle_num, cycle_group in cycle_groups:
                ct = cycle_group[COL_FRAME_TIME].values
                if len(ct) > 1:
                    duration = (ct[-1] - ct[0]) / np.timedelta64(1, 's')
                    all_per_cycle_durations.append(duration)

    df[COL_CUMULATIVE_RUNTIME] = cumulative

    ctx.unified_df = df
    ctx.runtime_info = RuntimeInfo(
        per_file_runtime=per_file_runtime,
        total_runtime_seconds=sum(per_file_runtime.values()),
        per_cycle_durations=all_per_cycle_durations,
        cumulative_runtime_column=COL_CUMULATIVE_RUNTIME,
    )
    return ctx
