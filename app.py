"""无人机电机可靠性测试数据分析 — Streamlit 入口"""

import streamlit as st

st.set_page_config(
    page_title="电机可靠性测试分析",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.state import init_state
from ui.sidebar import render_sidebar


def main():
    init_state()
    render_sidebar()

    st.sidebar.divider()
    st.sidebar.header("页面导航")

    page = st.sidebar.radio(
        "选择页面",
        ["概览", "时序探索", "台阶分析", "特征分析", "多文件对比", "退化趋势", "报告导出"],
    )

    if page == "概览":
        from ui.pages import overview
        overview.show()
    elif page == "时序探索":
        from ui.pages import timeseries
        timeseries.show()
    elif page == "台阶分析":
        from ui.pages import step_analysis
        step_analysis.show()
    elif page == "特征分析":
        from ui.pages import features
        features.show()
    elif page == "多文件对比":
        from ui.pages import comparison
        comparison.show()
    elif page == "退化趋势":
        from ui.pages import degradation
        degradation.show()
    elif page == "报告导出":
        from ui.pages import export
        export.show()


if __name__ == "__main__":
    main()
