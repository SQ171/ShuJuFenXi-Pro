"""SessionState 管理器 — 数据缓存与参数管理"""

import streamlit as st
from analysis.pipeline import AnalysisContext


def init_state():
    """初始化 session_state"""
    defaults = {
        "ctx": None,
        "data_loaded": False,
        "data_dir": "",
        "sigma": 2.5,
        "min_samples": 10,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_ctx() -> AnalysisContext | None:
    return st.session_state.get("ctx")


def set_ctx(ctx: AnalysisContext):
    st.session_state["ctx"] = ctx
    st.session_state["data_loaded"] = True


def is_data_loaded() -> bool:
    return st.session_state.get("data_loaded", False)
