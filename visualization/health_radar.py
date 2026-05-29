"""电机多维度健康雷达图"""

import plotly.graph_objects as go
import numpy as np
import pandas as pd
from core.models import Dimension
from visualization.common import FORCE_EFF_COLOR


_NO_DATA_FILL = 0.5


def plot_health_radar(scores: dict[str, float]) -> go.Figure:
    categories = list(scores.keys())
    values = list(scores.values())

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(220, 20, 60, 0.3)",
        line=dict(color=FORCE_EFF_COLOR, width=2),
        name="当前健康评分",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[1.0] * len(categories) + [1.0],
        theta=categories + [categories[0]],
        fill="none",
        line=dict(color="#CCCCCC", width=1, dash="dash"),
        name="满分线 (新电机)",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 1], tickfont=dict(size=10)),
            angularaxis=dict(direction="clockwise"),
        ),
        title=dict(text="电机健康雷达图", font=dict(size=16)),
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def compute_health_scores(degradation_results: list,
                          step_summary: pd.DataFrame) -> dict[str, float]:
    """根据 HEALTH_STANDARDS 计算各维度健康评分

    满血(1.0) = 新电机状态，报废(0.0) = 不合格
    退化率在 [failure, full_health] 区间线性映射
    """
    from config import HEALTH_STANDARDS

    scores = {}
    for dim in Dimension:
        std = HEALTH_STANDARDS.get(dim)
        if std is None:
            scores[dim.value] = _NO_DATA_FILL
            continue

        metric_key = std["metric"]
        throttle = std["throttle"]
        full = std["full_health"]
        fail = std["failure"]

        # 按指标名称跨维度匹配
        matched = [r for r in degradation_results
                   if r.analysis_type.value == "趋势分析"
                   and r.nominal_throttle == throttle
                   and r.metric_or_feature == metric_key]

        if not matched:
            scores[dim.value] = _NO_DATA_FILL
            continue

        slope = matched[0].slope_per_hour

        # health_direction: full > fail means higher is better
        # 线性映射: score = (slope - fail) / (full - fail)
        if full == fail:
            score = _NO_DATA_FILL
        else:
            score = (slope - fail) / (full - fail)
            score = float(np.clip(score, 0.0, 1.0))

        scores[dim.value] = score

    return scores
