"""Pipeline S6: 退化趋势分析"""

import numpy as np
import pandas as pd
from scipy import stats
from analysis.pipeline import AnalysisContext
from core.models import DegradationResult, DegradationReport, AnalysisType, Dimension
from config import ALL_METRICS, FEATURE_REGISTRY, DEGRADATION_MIN_SAMPLES

_DIM_RESULT_MAP = {
    Dimension.FORCE_EFF: "force_eff_results",
    Dimension.ELECTRICAL: "electrical_results",
    Dimension.MECHANICAL: "mechanical_results",
    Dimension.THERMAL: "thermal_results",
    Dimension.ENERGY: "energy_results",
}

_SIGNAL_DIM_MAP = {m.col_name: m.dimension for m in ALL_METRICS}


def analyze_degradation(ctx: AnalysisContext) -> AnalysisContext:
    report = DegradationReport()

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

                # 估算每个循环占用的时间 (小时)
                cycle_hours = ctx.runtime_info.total_runtime_seconds / 3600 / max(ctx.step_summary["cycle_num"].nunique(), 1)
                x = np.arange(len(values)) * cycle_hours
                result = _linear_regression(x, values, metric.display_name, metric.dimension,
                                            AnalysisType.TREND, throttle)
                if result:
                    _classify_result(report, result)

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

                        throttle_sub = throttle_sub.sort_values("cumulative_runtime")
                        values = throttle_sub["feature_value"].values
                        runtimes = throttle_sub["cumulative_runtime"].values

                        if len(values) < DEGRADATION_MIN_SAMPLES:
                            continue

                        display_name = f"{signal}-{feat_def.display_name}"
                        dim = _SIGNAL_DIM_MAP.get(signal, Dimension.MECHANICAL)

                        result = _linear_regression(
                            runtimes / 3600.0, values, display_name, dim,
                            feat_def.analysis_type, throttle
                        )
                        if result:
                            _classify_result(report, result)

    ctx.degradation_report = report
    return ctx


def _linear_regression(x: np.ndarray, y: np.ndarray, name: str,
                       dimension, analysis_type, throttle: float) -> DegradationResult | None:
    nan_mask = ~np.isnan(x) & ~np.isnan(y)
    x_clean = x[nan_mask]
    y_clean = y[nan_mask]

    if len(x_clean) < DEGRADATION_MIN_SAMPLES:
        return None

    slope, intercept, r_value, p_value, _ = stats.linregress(x_clean, y_clean)
    # x is already in hours, slope = Δy per hour
    slope_per_hour = slope

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
        data_points=len(x_clean),
    )


def _classify_result(report: DegradationReport, result: DegradationResult):
    report.results.append(result)
    attr = _DIM_RESULT_MAP.get(result.dimension)
    if attr:
        getattr(report, attr).append(result)
