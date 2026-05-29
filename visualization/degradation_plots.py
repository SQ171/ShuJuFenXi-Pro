"""退化趋势图：散点 + 回归线"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from core.models import DegradationResult, Dimension, AnalysisType
from core.constants import COL_CUMULATIVE_RUNTIME, COL_RUNTIME_HOURS
from config import ALL_METRICS
from visualization.common import base_layout, FORCE_EFF_COLOR, DIMENSION_COLORS, TREND_LINE_COLOR
from scipy import stats


def plot_metric_degradation(df: pd.DataFrame, metric_key: str,
                             throttle: float = None) -> go.Figure:
    from config import get_metric_by_key
    metric = get_metric_by_key(metric_key)
    if metric is None:
        return go.Figure()

    if COL_RUNTIME_HOURS not in df.columns and COL_CUMULATIVE_RUNTIME in df.columns:
        df = df.copy()
        df[COL_RUNTIME_HOURS] = df[COL_CUMULATIVE_RUNTIME] / 3600.0

    x_col = COL_RUNTIME_HOURS

    fig = go.Figure()
    values = df[[x_col, metric.col_name]].dropna()
    if len(values) < 5:
        return fig

    fig.add_trace(go.Scatter(
        x=values[x_col], y=values[metric.col_name],
        mode="markers", marker=dict(size=3, color=metric.chart_color, opacity=0.5),
        name=metric.display_name,
    ))

    if len(values) > 2:
        x_vals = values[x_col].values
        y_vals = values[metric.col_name].values
        slope, intercept, r_val, _, _ = stats.linregress(x_vals, y_vals)
        x_line = np.linspace(min(x_vals), max(x_vals), 100)
        y_line = slope * x_line + intercept
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode="lines",
            line=dict(color=TREND_LINE_COLOR, dash="dash", width=2),
            name=f"退化率: {slope:.4f}/h, R²={r_val**2:.3f}",
        ))

    title = f"{metric.display_name} - 退化趋势"
    if throttle is not None:
        title += f" @{throttle:.0f}%油门"

    fig.update_layout(base_layout(
        title, xlabel="累计运行时间 (h)", ylabel=f"{metric.display_name} ({metric.unit})",
        height=400,
    ))
    return fig


def plot_degradation_summary(results: list[DegradationResult]) -> go.Figure:
    f"""退化率汇总柱状图"""
    if not results:
        return go.Figure()

    by_throttle = {}
    for r in results:
        t = r.nominal_throttle
        if t not in by_throttle:
            by_throttle[t] = []
        by_throttle[t].append(r.slope_per_hour)

    throttles = sorted(by_throttle.keys())
    avg_slopes = [np.mean(by_throttle[t]) for t in throttles]

    colors = [FORCE_EFF_COLOR if s < 0 else "#2CA02C" for s in avg_slopes]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{t:.0f}%" for t in throttles],
        y=avg_slopes,
        marker_color=colors,
        text=[f"{s:.4f}" for s in avg_slopes],
        textposition="auto",
    ))

    fig.update_layout(base_layout(
        "退化率汇总 - 各油门台阶",
        xlabel="名义油门 (%)", ylabel="退化率 (per hour)",
        height=400,
    ))
    return fig
