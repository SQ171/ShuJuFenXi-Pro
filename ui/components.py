"""可复用组件：KPI卡片、数据表格、指标选择器"""

import streamlit as st
import pandas as pd
from config import ALL_METRICS, FEATURE_REGISTRY, get_metrics_by_dimension
from core.models import Dimension


def render_kpi_cards(ctx) -> None:
    cols = st.columns(4)
    if ctx.runtime_info:
        cols[0].metric("累计运行时间", f"{ctx.runtime_info.total_runtime_seconds/3600:.1f} h")
    cols[1].metric("数据文件数", len(ctx.test_runs))
    if ctx.step_summary is not None:
        cols[2].metric("总循环数", ctx.step_summary["cycle_num"].nunique())
    if ctx.step_summary is not None and "force_eff_mean" in ctx.step_summary.columns:
        avg_eff = ctx.step_summary["force_eff_mean"].mean()
        cols[3].metric("平均力效", f"{avg_eff:.1f} g/W")


def render_metric_selector(label: str = "选择指标", key: str = "metric_selector"):
    options = {m.display_name: m for m in ALL_METRICS}
    selected = st.selectbox(label, list(options.keys()), key=key)
    return options[selected]


def render_dimension_selector(label: str = "选择维度", key: str = "dim_selector"):
    dims = [d.value for d in Dimension]
    return st.selectbox(label, dims, key=key)


def render_signal_selector(label: str = "选择信号", key: str = "signal_selector"):
    signals = ["拉力-g", "电流-A", "扭矩-N•m", "光电转速-RPM"]
    return st.selectbox(label, signals, key=key)


def render_feature_type_selector(label: str = "选择特征类型", key: str = "feature_type"):
    return st.radio(label, ["时域统计", "频域特征"], key=key, horizontal=True)


def render_degradation_table(results: list, title: str = "退化分析结果") -> None:
    if not results:
        st.info("暂无退化分析数据")
        return

    st.subheader(title)
    rows = []
    for r in results:
        rows.append({
            "指标": r.metric_or_feature,
            "维度": r.dimension.value,
            "分析类型": r.analysis_type.value,
            "油门%": r.nominal_throttle,
            "退化率/h": f"{r.slope_per_hour:.4f}",
            "R²": f"{r.r_squared:.3f}",
            "显著": "是" if r.is_significant else "否",
            "样本数": r.data_points,
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
