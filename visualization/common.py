"""可视化共享工具：配色、字体、布局"""

import plotly.graph_objects as go

FORCE_EFF_COLOR = "#DC143C"
ANOMALY_COLOR = "#FF0000"
TREND_LINE_COLOR = "#2C3E50"
BG_COLOR = "#FFFFFF"
GRID_COLOR = "#E8E8E8"

DIMENSION_COLORS = {
    "力效": "#DC143C",
    "电气健康": "#FF7F0E",
    "机械健康": "#1F77B4",
    "热特征": "#FF4500",
    "能耗": "#7F7F7F",
}


def base_layout(title: str, xlabel: str = "", ylabel: str = "",
                height: int = 500) -> go.Layout:
    return go.Layout(
        title=dict(text=title, font=dict(size=16, color="#333333")),
        xaxis=dict(title=xlabel, gridcolor=GRID_COLOR, showgrid=True),
        yaxis=dict(title=ylabel, gridcolor=GRID_COLOR, showgrid=True),
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        height=height,
        hovermode="x unified",
        margin=dict(l=60, r=30, t=50, b=60),
    )


def add_anomaly_points(fig: go.Figure, x: list, y: list, name: str = "异常点"):
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="markers",
        marker=dict(color=ANOMALY_COLOR, size=8, symbol="x"),
        name=name,
    ))
