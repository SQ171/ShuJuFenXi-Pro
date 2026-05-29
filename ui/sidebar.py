"""侧边栏：文件上传、参数控制、导航"""

import os
import glob
import streamlit as st
from analysis.pipeline import AnalysisContext, run_pipeline
from ui.state import set_ctx, init_state


def render_sidebar():
    init_state()

    with st.sidebar:
        st.header("数据加载")

        data_dir = st.text_input(
            "CSV数据目录",
            value=st.session_state.get("data_dir", r"C:\Users\29432\Desktop\阶梯油门可靠性测试数据"),
            help="输入包含 MET-V6 CSV 文件的目录路径",
        )

        if st.button("加载数据", type="primary", use_container_width=True):
            if data_dir and os.path.isdir(data_dir):
                with st.spinner("正在加载数据..."):
                    files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
                    if not files:
                        st.error("未找到 CSV 文件")
                        return
                    ctx = run_pipeline(files)
                    set_ctx(ctx)
                    st.session_state["data_dir"] = data_dir
                    st.success(f"加载完成: {len(files)} 个文件, {ctx.runtime_info.total_runtime_seconds/3600:.2f}h")
            else:
                st.error("请选择有效的目录")

        st.divider()
        st.header("参数设置")

        sigma = st.slider("异常检测 σ 系数", 1.0, 5.0,
                          st.session_state.get("sigma", 2.5), 0.5,
                          help="偏离均值超过 N 倍标准差即标记为异常")
        st.session_state["sigma"] = sigma

        st.divider()

        if st.session_state.get("data_loaded", False):
            ctx = st.session_state.get("ctx")
            if ctx and ctx.runtime_info:
                ri = ctx.runtime_info
                st.metric("累计运行时间", f"{ri.total_runtime_seconds/3600:.1f} h")
                st.metric("文件数", len(ctx.test_runs))
                if ctx.step_summary is not None:
                    st.metric("循环数", ctx.step_summary["cycle_num"].nunique())
