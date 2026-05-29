"""退化趋势页 ★ 核心页面 — 按维度分Tab，三类分析结果汇总"""

import streamlit as st
from ui.state import get_ctx, is_data_loaded
from ui.components import render_degradation_table
from visualization.degradation_plots import plot_metric_degradation, plot_degradation_summary
from core.models import Dimension
from config import get_metrics_by_dimension


def show():
    st.title("退化趋势分析")
    st.caption("力效 | 电气健康 | 机械健康 | 热特征 | 能耗 — 趋势+时域+频域三层分析")

    if not is_data_loaded():
        st.info("请在侧边栏加载数据")
        return

    ctx = get_ctx()
    df = ctx.unified_df

    dims = [Dimension.FORCE_EFF, Dimension.ELECTRICAL, Dimension.MECHANICAL,
            Dimension.THERMAL, Dimension.ENERGY]

    tabs = st.tabs([d.value for d in dims])

    for i, dim in enumerate(dims):
        with tabs[i]:
            metrics = get_metrics_by_dimension(dim)
            if not metrics:
                st.info("该维度暂无指标")
                continue

            # 趋势图
            st.subheader("趋势分析 (均值 vs 运行时间)")
            for metric in metrics:
                if not metric.degradation_sensitive:
                    continue
                fig = plot_metric_degradation(df, metric.key)
                if fig.data:
                    st.plotly_chart(fig, use_container_width=True)

            # 退化汇总
            st.divider()
            results = ctx.degradation_report
            _DIM_ATTRS = {
                Dimension.FORCE_EFF: "force_eff_results",
                Dimension.ELECTRICAL: "electrical_results",
                Dimension.MECHANICAL: "mechanical_results",
                Dimension.THERMAL: "thermal_results",
                Dimension.ENERGY: "energy_results",
            }
            dim_results = getattr(results, _DIM_ATTRS.get(dim, ""), [])

            if dim_results:
                render_degradation_table(dim_results, f"{dim.value} 退化率汇总")

            st.divider()
            if dim_results:
                fig = plot_degradation_summary(dim_results)
                st.plotly_chart(fig, use_container_width=True)
