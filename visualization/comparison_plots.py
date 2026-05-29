"""多文件叠加对比图"""

import plotly.graph_objects as go
import numpy as np
import pandas as pd
from core.constants import COL_SOURCE_FILE, COL_CUMULATIVE_RUNTIME, COL_RUNTIME_HOURS
from config import ALL_METRICS
from core.models import MetricDef
from visualization.common import base_layout


def plot_multi_file_overlay(df: pd.DataFrame, metric: MetricDef,
                             file_filter: list[str] = None) -> go.Figure:
    if COL_RUNTIME_HOURS not in df.columns and COL_CUMULATIVE_RUNTIME in df.columns:
        df = df.copy()
        df[COL_RUNTIME_HOURS] = df[COL_CUMULATIVE_RUNTIME] / 3600.0

    x_col = COL_RUNTIME_HOURS
    sub = df if file_filter is None else df[df[COL_SOURCE_FILE].isin(file_filter)]

    fig = go.Figure()
    files = sorted(sub[COL_SOURCE_FILE].unique())
    colors = ["#1F77B4", "#DC143C", "#2CA02C", "#FF7F0E", "#9467BD", "#8C564B", "#17BECF"]

    for i, fname in enumerate(files):
        fdata = sub[sub[COL_SOURCE_FILE] == fname]
        values = fdata[[x_col, metric.col_name]].dropna()
        fig.add_trace(go.Scatter(
            x=values[x_col], y=values[metric.col_name],
            mode="lines", line=dict(color=colors[i % len(colors)], width=1.5),
            name=fname[:30],
        ))

    fig.update_layout(base_layout(
        f"{metric.display_name} - 多文件叠加对比",
        xlabel="累计运行时间 (h)", ylabel=f"{metric.display_name} ({metric.unit})",
        height=450,
    ))
    return fig
