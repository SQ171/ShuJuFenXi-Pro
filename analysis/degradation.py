"""Pipeline S6: 退化趋势分析 — 趋势+时域+频域三类特征分别回归"""

import numpy as np
import pandas as pd
from scipy import stats
from analysis.pipeline import AnalysisContext
from core.models import DegradationResult, DegradationReport, AnalysisType
from core.constants import COL_CUMULATIVE_RUNTIME
from config import ALL_METRICS, FEATURE_REGISTRY, DEGRADATION_MIN_SAMPLES


def analyze_degradation(ctx: AnalysisContext) -> AnalysisContext:
    report = DegradationReport()

    # ── 趋势分析：Metric 均值 vs 累计运行时间 ──
    if ctx.step_summary is not None and not ctx.step_summary.empty:
        for metric in ALL_METRICS:
            if not metric.degradation_sensitive:
                continue
            mean_col = f"{metric.key}_mean"
            if mean_col not in ctx.step_summary.columns:
                continue

            for throttle in sorted(ctx.step_summary["nominal_throttle"].dropna().unique()):
                subset = ctx.step_summary[ctx.step_summary["nominal_throttle"] == throttle]
                if len(subset) < DEGRADATION_MIN_SAMPLES:
                    continue
                values = subset[mean_col].dropna().values
                if len(values) < DEGRADATION_MIN_SAMPLES:
                    continue

                x = np.arange(len(values))
                result = _linear_regression(x, values, metric.display_name, metric.dimension,
                                            AnalysisType.TREND, throttle)
                if result:
                    _classify_result(report, result)

    # ── 时域+频域特征退化分析 ──
    if ctx.feature_results:
        features_df = pd.DataFrame([{
            "source_signal": fr.source_signal,
            "feature_key": fr.feature_key,
            "nominal_throttle": fr.nominal_throttle,
            "cycle_num": fr.cycle_num,
            "feature_value": fr.feature_value,
            "cumulative_runtime": fr.cumulative_runtime,
        } for fr in ctx.feature_results])

        if not features_df.empty:
            for feat_def in FEATURE_REGISTRY:
                for signal in feat_def.source_signals:
                    sub = features_df[
                        (features_df["feature_key"] == feat_def.key) &
                        (features_df["source_signal"] == signal)
                    ]
                    if len(sub) < DEGRADATION_MIN_SAMPLES:
                        continue

                    for throttle in sorted(sub["nominal_throttle"].dropna().unique()):
                        throttle_sub = sub[sub["nominal_throttle"] == throttle]
                        if len(throttle_sub) < DEGRADATION_MIN_SAMPLES:
                            continue

                        # 按累计运行时间排序
                        throttle_sub = throttle_sub.sort_values("cumulative_runtime")
                        values = throttle_sub["feature_value"].values
                        runtimes = throttle_sub["cumulative_runtime"].values

                        # 用累计运行时间(小时)作为x轴
                        if len(values) < DEGRADATION_MIN_SAMPLES:
                            continue
                        x_hours = runtimes / 3600.0

                        display_name = f"{signal}-{feat_def.display_name}"
                        # 判断归属维度
                        dim = _guess_dimension(signal)

                        result = _linear_regression(
                            x_hours, values, display_name, dim,
                            feat_def.analysis_type, throttle
                        )
                        if result:
                            _classify_result(report, result)

    ctx.degradation_report = report
    return ctx


def _linear_regression(x: np.ndarray, y: np.ndarray, name: str,
                       dimension, analysis_type, throttle: float) -> DegradationResult | None:
    if len(x) < DEGRADATION_MIN_SAMPLES or len(y) < DEGRADATION_MIN_SAMPLES:
        return None
    y = y[~np.isnan(y)]
    x = x[:len(y)] if len(x) > len(y) else x
    x = x[~np.isnan(x)]
    min_len = min(len(x), len(y))
    x, y = x[:min_len], y[:min_len]

    if len(x) < DEGRADATION_MIN_SAMPLES:
        return None

    slope, intercept, r_value, p_value, _ = stats.linregress(x, y)
    slope_per_hour = slope * 3600  # 如果x是秒，转为每小时

    return DegradationResult(
        metric_or_feature=name,
        dimension=dimension,
        analysis_type=analysis_type,
        nominal_throttle=throttle,
        slope=float(slope),
        slope_per_hour=float(slope_per_hour),
        r_squared=float(r_value ** 2),
        p_value=float(p_value),
        is_significant=p_value < 0.05,
        data_points=len(x),
    )


def _classify_result(report: DegradationReport, result: DegradationResult):
    report.results.append(result)
    dim = result.dimension
    if dim.value == "力效":
        report.force_eff_results.append(result)
    elif dim.value == "电气健康":
        report.electrical_results.append(result)
    elif dim.value == "机械健康":
        report.mechanical_results.append(result)
    elif dim.value == "热特征":
        report.thermal_results.append(result)
    elif dim.value == "能耗":
        report.energy_results.append(result)


def _guess_dimension(signal: str):
    from core.models import Dimension
    signal_map = {
        "拉力-g": Dimension.MECHANICAL,
        "扭矩-N•m": Dimension.MECHANICAL,
        "光电转速-RPM": Dimension.MECHANICAL,
        "电流-A": Dimension.ELECTRICAL,
        "电压-V": Dimension.ELECTRICAL,
        "红外温度-℃": Dimension.THERMAL,
    }
    return signal_map.get(signal, Dimension.MECHANICAL)
