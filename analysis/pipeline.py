"""Pipeline 引擎：按序执行分析步骤，通过 AnalysisContext 传递数据"""

from dataclasses import dataclass, field
import pandas as pd
from core.models import TestRun, RuntimeInfo, DegradationReport, FeatureResult


@dataclass
class AnalysisContext:
    file_paths: list[str] = field(default_factory=list)
    test_runs: list[TestRun] = field(default_factory=list)
    unified_df: pd.DataFrame | None = None
    runtime_info: RuntimeInfo | None = None
    step_summary: pd.DataFrame | None = None
    feature_results: list[FeatureResult] = field(default_factory=list)
    degradation_report: DegradationReport = field(default_factory=DegradationReport)
    anomaly_flags: pd.DataFrame | None = None
    comparison_table: pd.DataFrame | None = None


def run_pipeline(file_paths: list[str], ctx: AnalysisContext = None) -> AnalysisContext:
    if ctx is None:
        ctx = AnalysisContext(file_paths=file_paths)

    from analysis.loader import load_data
    from analysis.step_detector import detect_steps
    from analysis.runtime import compute_runtime
    from analysis.steady_state import compute_steady_state
    from analysis.features import extract_features
    from analysis.degradation import analyze_degradation
    from analysis.anomaly import detect_anomalies
    from analysis.comparator import compare_runs

    for step in [
        load_data,
        detect_steps,
        compute_runtime,
        compute_steady_state,
        extract_features,
        analyze_degradation,
        detect_anomalies,
        compare_runs,
    ]:
        ctx = step(ctx)

    return ctx
