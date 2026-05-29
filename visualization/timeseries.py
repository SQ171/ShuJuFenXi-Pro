"""全量时序图"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from core.constants import (
    COL_FRAME_TIME, COL_SYS_EFF, COL_THRUST, COL_IR_TEMP, COL_ELEC_POWER,
    COL_CUMULATIVE_RUNTIME, COL_RUNTIME_HOURS, COL_SOURCE_FILE,
)
from visualization.common import base_layout, FORCE_EFF_COLOR, add_anomaly_points


def plot_force_eff_timeseries(df: pd.DataFrame, highlight_anomalies: bool = True) -> go.Figure:
    x_col = COL_RUNTIME_HOURS if COL_RUNTIME_HOURS in df.columns else COL_CUMULATIVE_RUNTIME

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[COL_SYS_EFF],
        mode="lines", line=dict(color=FORCE_EFF_COLOR, width=1.5),
        name="系统力效",
    ))
    if highlight_anomalies and "is_outlier" in df.columns:
        outliers = df[df["is_outlier"] & (df[COL_SYS_EFF].notna())]
        if len(outliers) > 0:
            add_anomaly_points(fig, outliers[x_col], outliers[COL_SYS_EFF])

    fig.update_layout(base_layout(
        "系统力效 - 全量时序图",
        xlabel="累计运行时间 (h)", ylabel="系统力效 (g/W)",
        height=450,
    ))
    return fig


def plot_multi_signal_timeseries(df: pd.DataFrame, signals: list[str],
                                  file_filter: str = None) -> go.Figure:
    sub = df if file_filter is None else df[df[COL_SOURCE_FILE] == file_filter]
    x_col = COL_RUNTIME_HOURS if COL_RUNTIME_HOURS in sub.columns else COL_CUMULATIVE_RUNTIME

    fig = make_subplots(rows=len(signals), cols=1, shared_xaxes=True,
                        subplot_titles=signals, vertical_spacing=0.05)

    colors = ["#DC143C", "#1F77B4", "#FF7F0E", "#2CA02C", "#9467BD", "#8C564B", "#17BECF", "#FF4500"]
    for i, signal in enumerate(signals):
        if signal not in sub.columns:
            continue
        fig.add_trace(go.Scatter(
            x=sub[x_col], y=sub[signal],
            mode="lines", line=dict(color=colors[i % len(colors)], width=1),
            name=signal,
        ), row=i + 1, col=1)

    fig.update_layout(base_layout(
        "多信号时序图", xlabel="累计运行时间 (h)", height=300 * len(signals)
    ))
    return fig
