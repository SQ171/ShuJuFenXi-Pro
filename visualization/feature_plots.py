"""时域/频域特征趋势图、FFT频谱对比图"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from core.models import FeatureResult, FeatureDef
from core.constants import SAMPLING_RATE_HZ
from visualization.common import base_layout, DIMENSION_COLORS, TREND_LINE_COLOR
from scipy import stats


def plot_feature_trend(feature_results: list[FeatureResult],
                       feat_def: FeatureDef, signal: str,
                       throttle: float = None) -> go.Figure:
    data = [(fr.cycle_num, fr.cumulative_runtime, fr.feature_value)
            for fr in feature_results
            if fr.feature_key == feat_def.key and fr.source_signal == signal
            and (throttle is None or fr.nominal_throttle == throttle)]

    if not data:
        return go.Figure()

    cycles, runtimes, values = zip(*data)
    runtimes_h = np.array(runtimes) / 3600.0
    values = np.array(values)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=runtimes_h, y=values, mode="markers",
        marker=dict(size=6, color=DIMENSION_COLORS.get("机械健康", "#1F77B4")),
        name=f"{signal}-{feat_def.display_name}",
    ))

    if len(values) > 2:
        slope, intercept, r_val, _, _ = stats.linregress(runtimes_h, values)
        x_line = np.linspace(min(runtimes_h), max(runtimes_h), 100)
        y_line = slope * x_line + intercept
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode="lines",
            line=dict(color=TREND_LINE_COLOR, dash="dash", width=2),
            name=f"退化率: {slope:.4f}/h (R²={r_val**2:.3f})",
        ))

    title = f"{signal} - {feat_def.display_name} 趋势"
    if throttle is not None:
        title += f" @{throttle:.0f}%油门"

    fig.update_layout(base_layout(
        title, xlabel="累计运行时间 (h)", ylabel=feat_def.display_name,
        height=400,
    ))
    return fig


def plot_fft_comparison(df: pd.DataFrame, signal: str,
                         cycle_a: int, cycle_b: int = None,
                         file_filter: str = None) -> go.Figure:
    from core.constants import (
        COL_CYCLE_NUM, COL_IS_STABILIZING, COL_SOURCE_FILE, COL_STEP_ID
    )
    sub = df if file_filter is None else df[df[COL_SOURCE_FILE] == file_filter]
    stable = sub[~sub[COL_IS_STABILIZING]]

    if signal not in stable.columns:
        return go.Figure()

    def get_fft(cycle_num):
        cycle_data = stable[stable[COL_CYCLE_NUM] == cycle_num]
        if cycle_data.empty:
            return None, None
        values = cycle_data[signal].dropna().values
        if len(values) < 10:
            return None, None
        vals = values - np.mean(values)
        n = len(vals)
        fft = np.abs(np.fft.rfft(vals))
        freqs = np.fft.rfftfreq(n, 1.0 / SAMPLING_RATE_HZ)
        return freqs[1:], fft[1:]  # skip DC

    freqs_a, mags_a = get_fft(cycle_a)
    if freqs_a is None:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=freqs_a, y=mags_a, mode="lines",
        name=f"循环 {cycle_a}", line=dict(color="#1F77B4", width=1.5),
    ))

    if cycle_b is not None:
        freqs_b, mags_b = get_fft(cycle_b)
        if freqs_b is not None:
            fig.add_trace(go.Scatter(
                x=freqs_b, y=mags_b, mode="lines",
                name=f"循环 {cycle_b}", line=dict(color="#DC143C", width=1.5),
            ))

    fig.update_layout(base_layout(
        f"{signal} - FFT频谱对比 (循环{cycle_a} vs {cycle_b or 'N/A'})",
        xlabel="频率 (Hz)", ylabel="幅值",
        height=400,
    ))
    return fig


def plot_feature_heatmap(feature_results: list[FeatureResult],
                          feat_def: FeatureDef, signal: str) -> go.Figure:
    data = [(fr.cycle_num, fr.nominal_throttle, fr.feature_value)
            for fr in feature_results
            if fr.feature_key == feat_def.key and fr.source_signal == signal]

    if not data:
        return go.Figure()

    df = pd.DataFrame(data, columns=["cycle", "throttle", "value"])
    pivot = df.pivot_table(values="value", index="throttle", columns="cycle", aggfunc="mean")

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"循环{c}" for c in pivot.columns],
        y=[f"{t:.0f}%" for t in pivot.index],
        colorscale="RdBu_r",
        colorbar_title=feat_def.display_name,
    ))

    fig.update_layout(base_layout(
        f"{signal} - {feat_def.display_name} 热力图",
        xlabel="循环序号", ylabel="名义油门 (%)",
        height=450,
    ))
    return fig
