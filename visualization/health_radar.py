"""电机多维度健康雷达图"""

import plotly.graph_objects as go
import numpy as np
import pandas as pd
from core.models import Dimension


def plot_health_radar(scores: dict[str, float]) -> go.Figure:
    """绘制五维健康雷达图

    Args:
        scores: {"力效": 0.85, "电气健康": 0.72, "机械健康": 0.68, "热特征": 0.90, "能耗": 0.75}
                值范围 0-1，1=最佳健康状态
    """
    categories = list(scores.keys())
    values = list(scores.values())

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # 闭合成环
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(220, 20, 60, 0.3)",
        line=dict(color="#DC143C", width=2),
        name="当前健康评分",
    ))

    # 添加参考线 (满分)
    fig.add_trace(go.Scatterpolar(
        r=[1.0] * len(categories) + [1.0],
        theta=categories + [categories[0]],
        fill="none",
        line=dict(color="#CCCCCC", width=1, dash="dash"),
        name="基准线",
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


def compute_health_scores(degradation_results: list, step_summary: pd.DataFrame) -> dict[str, float]:
    """根据退化分析结果计算各维度健康评分 (0-1, 1=最健康)"""
    scores = {}
    for dim in Dimension:
        dim_results = [r for r in degradation_results if r.dimension == dim]
        if not dim_results:
            scores[dim.value] = 0.8  # 无数据时默认中等
            continue

        avg_r2 = np.mean([r.r_squared for r in dim_results])
        avg_slope = np.mean([abs(r.slope_per_hour) for r in dim_results])

        r2_score = max(0, 1.0 - avg_r2)  # R²越低越不确定，扣分越少
        slope_score = max(0, 1.0 - avg_slope * 100)  # 退化率越大扣分越多

        score = 0.5 * r2_score + 0.5 * slope_score
        scores[dim.value] = float(np.clip(score, 0.0, 1.0))

    return scores
