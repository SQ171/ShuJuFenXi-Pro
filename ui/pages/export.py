"""报告导出页"""

import streamlit as st
from ui.state import get_ctx, is_data_loaded


def show():
    st.title("报告导出")
    if not is_data_loaded():
        st.info("请在侧边栏加载数据")
        return

    ctx = get_ctx()

    st.subheader("Excel 导出")
    if st.button("导出 Excel 报告", type="primary"):
        try:
            from export.excel_exporter import export_to_excel
            import os
            output = os.path.expanduser("~/Desktop/电机测试分析报告.xlsx")
            export_to_excel(ctx, output)
            st.success(f"已导出到: {output}")
        except Exception as e:
            st.error(f"导出失败: {e}")

    st.divider()
    st.subheader("HTML 报告预览")
    st.info("HTML报告生成功能将在Phase 6完成")

    if ctx.step_summary is not None and not ctx.step_summary.empty:
        st.subheader("数据预览")
        st.dataframe(ctx.step_summary.head(20), use_container_width=True)
