"""无人机电机可靠性测试数据分析 — Streamlit 入口"""

import streamlit as st

st.set_page_config(
    page_title="电机可靠性测试分析",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.state import init_state
from ui.sidebar import render_sidebar

PAGES = {
    "概览": "ui.pages.overview",
    "时序探索": "ui.pages.timeseries",
    "台阶分析": "ui.pages.step_analysis",
    "特征分析": "ui.pages.features",
    "多文件对比": "ui.pages.comparison",
    "退化趋势": "ui.pages.degradation",
    "报告导出": "ui.pages.export",
}


def main():
    init_state()
    render_sidebar()

    st.sidebar.divider()
    st.sidebar.header("页面导航")
    page = st.sidebar.radio("选择页面", list(PAGES.keys()))

    module = __import__(PAGES[page], fromlist=["show"])
    module.show()


if __name__ == "__main__":
    main()
