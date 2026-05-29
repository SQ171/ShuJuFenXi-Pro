"""概览页：KPI卡片 + 健康雷达图 + 摘要"""

import streamlit as st
from ui.state import get_ctx, is_data_loaded
from ui.components import render_kpi_cards
from visualization.health_radar import plot_health_radar, compute_health_scores


def show():
    st.title("测试概览")
    if not is_data_loaded():
        st.info("请在侧边栏加载数据")
        return

    ctx = get_ctx()
    render_kpi_cards(ctx)

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("电机健康雷达图")
        if ctx.degradation_report and ctx.degradation_report.results:
            scores = compute_health_scores(
                ctx.degradation_report.results, ctx.step_summary
            )
            fig = plot_health_radar(scores)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("退化分析数据不足")

    with col2:
        st.subheader("测试信息")
        if ctx.test_runs:
            for run in ctx.test_runs:
                with st.expander(f"{run.filename}"):
                    st.write(f"开始时间: {run.start_time}")
                    st.write(f"结束时间: {run.end_time}")
                    st.write(f"持续时长: {run.duration_seconds/60:.1f} 分钟")
                    st.write(f"数据行数: {len(run.df)}")
                    if run.metadata:
                        st.write(f"环境温度: {run.metadata.get('环境温度', 'N/A')}")
                        st.write(f"环境湿度: {run.metadata.get('环境湿度', 'N/A')}")
