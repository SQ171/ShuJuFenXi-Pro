"""Pipeline S2: 油门台阶检测 + 循环编号 + 稳定窗口标记"""

import numpy as np
import pandas as pd
from analysis.pipeline import AnalysisContext
from core.constants import (
    COL_THROTTLE, COL_STEP_ID, COL_NOMINAL_THROTTLE,
    COL_CYCLE_NUM, COL_IS_STABILIZING, COL_FRAME_TIME,
    COL_SOURCE_FILE, THROTTLE_STEPS, SAMPLING_RATE_HZ,
    STABILIZATION_SECONDS, MIN_STEP_DURATION_SECONDS,
)


def detect_steps(ctx: AnalysisContext) -> AnalysisContext:
    df = ctx.unified_df
    if df is None or df.empty:
        return ctx

    df = df.sort_values([COL_SOURCE_FILE, COL_FRAME_TIME]).reset_index(drop=True)

    all_results = []
    for filename, group in df.groupby(COL_SOURCE_FILE):
        group = group.sort_values(COL_FRAME_TIME).reset_index(drop=True)
        result = _detect_steps_single(group, filename)
        all_results.append(result)

    ctx.unified_df = pd.concat(all_results, ignore_index=True)
    return ctx


def _detect_steps_single(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    throttle_values = df[COL_THROTTLE].values
    n = len(df)

    if n == 0:
        return df

    step_ids = np.full(n, -1, dtype=int)
    nominal_throttles = np.full(n, np.nan)
    cycle_nums = np.full(n, -1, dtype=int)
    is_stabilizing = np.full(n, False)

    # 扫描油门变化，检测过渡事件和循环重置
    transition_events = []
    step_start_idx = 0
    prev_throttle = throttle_values[0]

    for i in range(1, n):
        delta = abs(throttle_values[i] - prev_throttle)
        if delta > 2.0:
            step_duration = (i - step_start_idx) / SAMPLING_RATE_HZ
            if step_duration >= MIN_STEP_DURATION_SECONDS:
                transition_events.append(i)
                step_start_idx = i

        if throttle_values[i - 1] > 50 and throttle_values[i] < 25:
            transition_events.append(i)

        prev_throttle = throttle_values[i]

    # 根据过渡事件分配标签
    if not transition_events:
        # 全文件只有一个段
        nom_throttle = _round_to_nearest_step(np.median(throttle_values))
        step_ids[:] = 0
        nominal_throttles[:] = nom_throttle
        cycle_nums[:] = 0
    else:
        current_step = 0
        current_cycle = 0
        seg_start = 0

        for trans_idx in transition_events:
            # 分配前一段
            seg_throttle_vals = throttle_values[seg_start:trans_idx]
            if len(seg_throttle_vals) > 0:
                nom_throttle = _round_to_nearest_step(np.median(seg_throttle_vals))
                step_ids[seg_start:trans_idx] = current_step
                nominal_throttles[seg_start:trans_idx] = nom_throttle
                cycle_nums[seg_start:trans_idx] = current_cycle

                # 标记稳定窗口（过渡后前N秒）
                stab_end = min(seg_start + int(STABILIZATION_SECONDS * SAMPLING_RATE_HZ), trans_idx)
                is_stabilizing[seg_start:stab_end] = True

            # 检测是否是循环重置
            if seg_start > 0 and throttle_values[seg_start - 1] > 50 and throttle_values[seg_start] < 25:
                current_cycle += 1
                current_step = 0
            else:
                current_step += 1

            seg_start = trans_idx

        # 分配最后一段
        if seg_start < n:
            seg_throttle_vals = throttle_values[seg_start:]
            nom_throttle = _round_to_nearest_step(np.median(seg_throttle_vals))
            step_ids[seg_start:] = current_step
            nominal_throttles[seg_start:] = nom_throttle
            cycle_nums[seg_start:] = current_cycle
            stab_end = min(seg_start + int(STABILIZATION_SECONDS * SAMPLING_RATE_HZ), n)
            is_stabilizing[seg_start:stab_end] = True

    df[COL_STEP_ID] = step_ids
    df[COL_NOMINAL_THROTTLE] = nominal_throttles
    df[COL_CYCLE_NUM] = cycle_nums
    df[COL_IS_STABILIZING] = is_stabilizing
    return df


def _round_to_nearest_step(value: float) -> float:
    return min(THROTTLE_STEPS, key=lambda s: abs(s - value))
