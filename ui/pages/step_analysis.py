"""台阶分析页"""

import streamlit as st
from ui.state import get_ctx, is_data_loaded
from ui.components import render_metric_selector
from visualization.step_plots import plot_step_boxplot, plot_step_bar, plot_multi_file_step_comparison


def show():
    st.title("油门台阶分析")
    if not is_data_loaded():
        st.info("请在侧边栏加载数据")
        return

    ctx = get_ctx()
    ss = ctx.step_summary

    if ss is None or ss.empty:
        st.warning("台阶数据为空")
        return

    metric = render_metric_selector("选择指标", key="step_metric")

    tab1, tab2, tab3 = st.tabs(["箱线图", "均值柱状图", "多文件对比"])

    with tab1:
        fig = plot_step_boxplot(ss, metric)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = plot_step_bar(ss, metric)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        if ctx.comparison_table is not None and not ctx.comparison_table.empty:
            fig = plot_multi_file_step_comparison(
                ctx.comparison_table, metric.key, metric.display_name, metric.unit
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("无对比数据")
