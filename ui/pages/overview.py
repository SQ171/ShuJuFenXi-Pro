"""概览页：KPI卡片 + 力效对比 + 健康雷达图"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from ui.state import get_ctx, is_data_loaded
from ui.components import render_kpi_cards
from visualization.health_radar import plot_health_radar, compute_health_scores
from visualization.common import base_layout, FORCE_EFF_COLOR
from config import get_metric_by_key


def show():
    st.title("测试概览")
    if not is_data_loaded():
        st.info("请在侧边栏加载数据")
        return

    ctx = get_ctx()
    render_kpi_cards(ctx)

    st.divider()

    # ── 力效对比与趋势 ──
    st.subheader("力效 @40%油门 — 跨时段对比与趋势")
    if ctx.step_summary is not None and "force_eff_mean" in ctx.step_summary.columns:
        ss_40 = ctx.step_summary[ctx.step_summary["nominal_throttle"] == 40.0].copy()
        if not ss_40.empty:
            col1, col2 = st.columns([1, 2])

            with col1:
                _render_file_comparison(ctx, ss_40)

            with col2:
                _render_eff_trend(ss_40)

    st.divider()

    # ── 健康雷达 + 测试信息 ──
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("电机健康雷达图")
        if ctx.degradation_report and ctx.degradation_report.results:
            scores = compute_health_scores(
                ctx.degradation_report.results, ctx.step_summary
            )
            fig = plot_health_radar(scores)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("测试文件信息")
        if ctx.test_runs:
            for run in ctx.test_runs:
                eff_val = ""
                if ss_40 is not None and not ss_40.empty:
                    file_eff = ss_40[ss_40["source_file"] == run.filename]
                    if not file_eff.empty:
                        eff_val = f" | 力效均值: {file_eff['force_eff_mean'].mean():.1f} g/W"

                with st.expander(f"{run.filename}{eff_val}"):
                    st.write(f"开始: {run.start_time}")
                    st.write(f"结束: {run.end_time}")
                    st.write(f"持续: {run.duration_seconds/60:.1f} min")


def _render_file_comparison(ctx, ss_40):
    """各测试文件的力效对比柱状图"""
    files = ss_40["source_file"].unique()
    means = []
    stds = []
    labels = []
    for f in files:
        sub = ss_40[ss_40["source_file"] == f]["force_eff_mean"]
        means.append(sub.mean())
        stds.append(sub.std())
        # 截短文件名
        labels.append(f.replace(".csv", "")[-8:])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=means,
        error_y=dict(type="data", array=stds),
        marker_color=FORCE_EFF_COLOR,
        text=[f"{m:.1f}" for m in means],
        textposition="auto",
    ))

    # 用退化分析结果标注退化率
    for r in ctx.degradation_report.force_eff_results:
        if r.nominal_throttle == 40.0:
            st.caption(f"退化率: {r.slope_per_hour:.4f} g/W/h | R²={r.r_squared:.3f} | p={r.p_value:.4f}")
            break

    fig.update_layout(base_layout("各文件力效均值对比", xlabel="文件", ylabel="力效 (g/W)", height=350))
    st.plotly_chart(fig, use_container_width=True)


def _render_eff_trend(ss_40):
    """力效随循环变化趋势（同一时段内的变化）"""
    ss_40 = ss_40.sort_values(["source_file", "cycle_num"])
    files = ss_40["source_file"].unique()

    fig = go.Figure()
    colors = ["#DC143C", "#1F77B4", "#2CA02C", "#FF7F0E", "#9467BD"]

    for i, f in enumerate(files):
        sub = ss_40[ss_40["source_file"] == f]
        fig.add_trace(go.Scatter(
            y=sub["force_eff_mean"], mode="lines+markers",
            name=f.replace(".csv", ""), marker=dict(size=4),
            line=dict(color=colors[i % len(colors)], width=1.5),
        ))

    fig.update_layout(base_layout(
        "力效随循环变化趋势 @40%油门",
        xlabel="循环序号", ylabel="力效 (g/W)", height=350,
    ))
    st.plotly_chart(fig, use_container_width=True)
