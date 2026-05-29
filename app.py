"""无人机电机可靠性测试数据分析 — Streamlit 入口"""

import streamlit as st

st.set_page_config(
    page_title="电机可靠性测试分析",
    page_icon=":helicopter:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.state import init_state
from ui.sidebar import render_sidebar


def main():
    init_state()

    # Build navigation
    pages = {
        "概览": "ui.pages.overview",
        "时序探索": "ui.pages.timeseries",
        "台阶分析": "ui.pages.step_analysis",
        "特征分析": "ui.pages.features",
        "多文件对比": "ui.pages.comparison",
        "退化趋势": "ui.pages.degradation",
        "报告导出": "ui.pages.export",
    }

    render_sidebar()

    pg = st.navigation([
        st.Page(f"{module}.show", title=name, icon=icon)
        for name, module, icon in [
            ("概览", "ui.pages.overview", ":material/dashboard:"),
            ("时序探索", "ui.pages.timeseries", ":material/timeline:"),
            ("台阶分析", "ui.pages.step_analysis", ":material/analytics:"),
            ("特征分析", "ui.pages.features", ":material/bar_chart:"),
            ("多文件对比", "ui.pages.comparison", ":material/compare_arrows:"),
            ("退化趋势", "ui.pages.degradation", ":material/trending_down:"),
            ("报告导出", "ui.pages.export", ":material/download:"),
        ]
    ])
    pg.run()


if __name__ == "__main__":
    main()
