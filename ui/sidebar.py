"""侧边栏：文件上传、参数控制、导航"""

import os
import tempfile
import streamlit as st
from analysis.pipeline import run_pipeline
from ui.state import set_ctx, init_state


def render_sidebar():
    init_state()

    with st.sidebar:
        st.header("数据加载")

        uploaded_files = st.file_uploader(
            "选择 CSV 文件",
            type=["csv"],
            accept_multiple_files=True,
            help="可多选或拖拽 MET-V6 测试台 CSV 文件",
        )

        if st.button("加载数据", type="primary", use_container_width=True):
            if uploaded_files:
                with st.spinner("正在加载数据..."):
                    tmpdir = tempfile.mkdtemp()
                    file_paths = []
                    for uploaded in uploaded_files:
                        tmp_path = os.path.join(tmpdir, uploaded.name)
                        with open(tmp_path, "wb") as f:
                            f.write(uploaded.getbuffer())
                        file_paths.append(tmp_path)

                    sigma = st.session_state.get("sigma", 2.5)
                    ctx = run_pipeline(file_paths, sigma=sigma)
                    set_ctx(ctx)
                    st.success(f"加载完成: {len(file_paths)} 个文件, "
                               f"{ctx.runtime_info.total_runtime_seconds/3600:.2f}h")
            else:
                st.error("请先选择 CSV 文件")

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
