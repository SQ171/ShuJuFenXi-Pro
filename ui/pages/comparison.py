"""多文件对比页"""

import streamlit as st
from ui.state import get_ctx, is_data_loaded
from ui.components import render_metric_selector
from visualization.comparison_plots import plot_multi_file_overlay
from visualization.step_plots import plot_multi_file_step_comparison
from core.constants import COL_SOURCE_FILE


def show():
    st.title("多文件对比")
    if not is_data_loaded():
        st.info("请在侧边栏加载数据")
        return

    ctx = get_ctx()
    df = ctx.unified_df

    files = sorted(df[COL_SOURCE_FILE].unique())
    selected_files = st.multiselect("选择对比文件", files, default=files[:min(5, len(files))])

    if not selected_files:
        st.warning("请选择至少一个文件")
        return

    metric = render_metric_selector("选择指标", key="comp_metric")

    tab1, tab2 = st.tabs(["时序叠加", "台阶对比"])

    with tab1:
        fig = plot_multi_file_overlay(df, metric, selected_files)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if ctx.comparison_table is not None and not ctx.comparison_table.empty:
            fig = plot_multi_file_step_comparison(
                ctx.comparison_table, metric.key, metric.display_name, metric.unit
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("无对比数据")
