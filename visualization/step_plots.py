"""台阶稳态分布图：箱线图 + 柱状图 + 误差棒"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from config import ALL_METRICS
from core.models import MetricDef
from visualization.common import base_layout


def plot_step_boxplot(step_summary: pd.DataFrame, metric: MetricDef) -> go.Figure:
    mean_col = f"{metric.key}_mean"
    if mean_col not in step_summary.columns:
        return go.Figure()

    data = step_summary[["nominal_throttle", mean_col]].dropna()
    throttles = sorted(data["nominal_throttle"].unique())

    fig = go.Figure()
    for t in throttles:
        values = data[data["nominal_throttle"] == t][mean_col]
        fig.add_trace(go.Box(
            y=values, name=f"{t:.0f}%",
            marker_color=metric.chart_color,
            boxmean="sd",
        ))

    fig.update_layout(base_layout(
        f"{metric.display_name} - 各油门台阶分布",
        xlabel="名义油门 (%)", ylabel=f"{metric.display_name} ({metric.unit})",
        height=450,
    ))
    return fig


def plot_step_bar(step_summary: pd.DataFrame, metric: MetricDef) -> go.Figure:
    mean_col = f"{metric.key}_mean"
    std_col = f"{metric.key}_std"
    if mean_col not in step_summary.columns:
        return go.Figure()

    throttles = sorted(step_summary["nominal_throttle"].dropna().unique())
    means = []
    stds = []
    for t in throttles:
        sub = step_summary[step_summary["nominal_throttle"] == t]
        means.append(sub[mean_col].mean())
        stds.append(sub[std_col].mean() if std_col in sub.columns else 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{t:.0f}%" for t in throttles],
        y=means,
        error_y=dict(type="data", array=stds, visible=True),
        marker_color=metric.chart_color,
        name=metric.display_name,
    ))

    fig.update_layout(base_layout(
        f"{metric.display_name} - 各油门台阶均值",
        xlabel="名义油门 (%)", ylabel=f"{metric.display_name} ({metric.unit})",
        height=400,
    ))
    return fig


def plot_multi_file_step_comparison(comparison_table: pd.DataFrame, metric_key: str,
                                     display_name: str, unit: str) -> go.Figure:
    sub = comparison_table[comparison_table["metric"] == display_name]
    if sub.empty:
        return go.Figure()

    files = sorted(sub["source_file"].unique())
    throttles = sorted(sub["nominal_throttle"].unique())

    fig = go.Figure()
    for file in files:
        file_data = sub[sub["source_file"] == file]
        y_vals = []
        for t in throttles:
            td = file_data[file_data["nominal_throttle"] == t]
            y_vals.append(td["mean"].values[0] if len(td) > 0 else None)

        fig.add_trace(go.Scatter(
            x=[f"{t:.0f}%" for t in throttles],
            y=y_vals, mode="lines+markers",
            name=file[:25],  # trunctate long names
        ))

    fig.update_layout(base_layout(
        f"{display_name} - 多文件对比",
        xlabel="名义油门 (%)", ylabel=f"{display_name} ({unit})",
        height=450,
    ))
    return fig
