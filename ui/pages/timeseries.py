"""时序探索页"""

import streamlit as st
from ui.state import get_ctx, is_data_loaded
from visualization.timeseries import plot_force_eff_timeseries, plot_multi_signal_timeseries
from core.constants import COL_SYS_EFF, COL_THRUST, COL_IR_TEMP, COL_ELEC_POWER, COL_CURRENT


def show():
    st.title("时序数据探索")
    if not is_data_loaded():
        st.info("请在侧边栏加载数据")
        return

    ctx = get_ctx()
    df = ctx.unified_df

    tab1, tab2 = st.tabs(["力效时序", "多信号对比"])

    with tab1:
        st.subheader("系统力效 - 全量时序")
        fig = plot_force_eff_timeseries(df)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("多信号同步对比")
        selected_signals = st.multiselect(
            "选择信号", [COL_SYS_EFF, COL_THRUST, COL_CURRENT, COL_ELEC_POWER, COL_IR_TEMP],
            default=[COL_SYS_EFF, COL_THRUST],
        )
        if selected_signals:
            fig = plot_multi_signal_timeseries(df, selected_signals)
            st.plotly_chart(fig, use_container_width=True)
