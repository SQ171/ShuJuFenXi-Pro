"""领域数据模型 — 所有模块间的数据契约"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import pandas as pd


class Dimension(Enum):
    FORCE_EFF = "力效"
    ELECTRICAL = "电气健康"
    MECHANICAL = "机械健康"
    THERMAL = "热特征"
    ENERGY = "能耗"


class AnalysisType(Enum):
    TREND = "趋势分析"
    TIME_DOMAIN = "时域统计"
    FREQ_DOMAIN = "频域特征"


class HealthDirection(Enum):
    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"
    STABLE_BETTER = "stable_better"


@dataclass
class MetricDef:
    key: str
    col_name: str
    unit: str
    display_name: str
    dimension: Dimension
    is_primary: bool = False
    degradation_sensitive: bool = True
    chart_color: str = "#1F77B4"
    health_direction: HealthDirection = HealthDirection.STABLE_BETTER


@dataclass
class FeatureDef:
    key: str
    display_name: str
    analysis_type: AnalysisType
    unit: str
    source_signals: list[str] = field(default_factory=list)
    health_direction: HealthDirection = HealthDirection.STABLE_BETTER


@dataclass
class ParsedData:
    metadata: dict
    df: pd.DataFrame


@dataclass
class TestRun:
    filename: str
    filepath: str
    file_info: dict
    metadata: dict
    df: pd.DataFrame
    start_time: datetime | None
    end_time: datetime | None
    duration_seconds: float
    correction_factor: float = 1.0


@dataclass
class RuntimeInfo:
    per_file_runtime: dict[str, float]
    total_runtime_seconds: float
    per_cycle_durations: list[float]
    cumulative_runtime_column: str


@dataclass
class StepSummary:
    source_file: str
    cycle_num: int
    step_id: int
    nominal_throttle: float
    sample_count: int
    stabilization_count: int
    metric_stats: dict


@dataclass
class FeatureResult:
    step_id: int
    nominal_throttle: float
    cycle_num: int
    source_file: str
    source_signal: str
    feature_key: str
    feature_value: float
    cumulative_runtime: float


@dataclass
class DegradationResult:
    metric_or_feature: str
    dimension: Dimension
    analysis_type: AnalysisType
    nominal_throttle: float
    slope: float
    slope_per_hour: float
    r_squared: float
    p_value: float
    is_significant: bool
    data_points: int


@dataclass
class DegradationReport:
    results: list[DegradationResult] = field(default_factory=list)
    force_eff_results: list[DegradationResult] = field(default_factory=list)
    electrical_results: list[DegradationResult] = field(default_factory=list)
    mechanical_results: list[DegradationResult] = field(default_factory=list)
    thermal_results: list[DegradationResult] = field(default_factory=list)
    energy_results: list[DegradationResult] = field(default_factory=list)
