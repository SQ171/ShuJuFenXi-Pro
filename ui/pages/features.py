"""时域/频域特征专项分析页"""

import streamlit as st
from ui.state import get_ctx, is_data_loaded
from ui.components import render_signal_selector
from visualization.feature_plots import plot_feature_trend, plot_fft_comparison, plot_feature_heatmap
from config import FEATURE_REGISTRY, get_features_for_signal
from core.models import AnalysisType


def show():
    st.title("时域/频域特征分析")
    if not is_data_loaded():
        st.info("请在侧边栏加载数据")
        return

    ctx = get_ctx()

    col1, col2 = st.columns(2)
    with col1:
        signal = render_signal_selector(key="feat_signal")
    with col2:
        analysis_type = st.radio("特征类型", ["时域统计", "频域特征"],
                                  key="feat_type", horizontal=True)

    at = AnalysisType.TIME_DOMAIN if analysis_type == "时域统计" else AnalysisType.FREQ_DOMAIN
    relevant_features = [f for f in FEATURE_REGISTRY
                         if f.analysis_type == at and signal in f.source_signals]

    if not relevant_features:
        st.info(f"该信号无{analysis_type}特征")
        return

    feat_names = [f.display_name for f in relevant_features]
    selected_feat_name = st.selectbox("选择特征", feat_names)
    selected_feat = next(f for f in relevant_features if f.display_name == selected_feat_name)

    tab1, tab2, tab3 = st.tabs(["特征趋势", "FFT频谱对比", "特征热力图"])

    with tab1:
        throttle = st.selectbox(
            "选择油门台阶 (可选全部)",
            ["全部"] + sorted([f"{t:.0f}%"
                               for t in set(fr.nominal_throttle for fr in ctx.feature_results
                                            if fr.feature_key == selected_feat.key and fr.source_signal == signal)]),
        )
        t_val = float(throttle.replace("%", "")) if throttle != "全部" else None
        fig = plot_feature_trend(ctx.feature_results, selected_feat, signal, t_val)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if at == AnalysisType.FREQ_DOMAIN:
            col_a, col_b = st.columns(2)
            file_names = sorted(ctx.unified_df["数据来源"].unique())
            with col_a:
                cycle_a = st.number_input("循环A", min_value=0, value=0, key="fft_cycle_a")
            with col_b:
                cycle_b = st.number_input("循环B (对比)", min_value=0, value=10, key="fft_cycle_b")

            fig = plot_fft_comparison(ctx.unified_df, signal, cycle_a, cycle_b)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("频域对比仅适用于频域特征分析")

    with tab3:
        fig = plot_feature_heatmap(ctx.feature_results, selected_feat, signal)
        st.plotly_chart(fig, use_container_width=True)
