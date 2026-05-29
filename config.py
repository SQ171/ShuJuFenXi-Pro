"""全局注册中心：维度、指标、特征、阈值、配色"""

from core.models import Dimension, AnalysisType, HealthDirection, MetricDef, FeatureDef

# ═══════════════════════════════════════════════════════════════
# 监测指标注册 — 新增指标只需加一行
# ═══════════════════════════════════════════════════════════════

ALL_METRICS: list[MetricDef] = [
    # ── 力效（核心） ──
    MetricDef("force_eff", "系统力效-g/W", "g/W", "系统力效",
              Dimension.FORCE_EFF, is_primary=True, degradation_sensitive=True,
              chart_color="#DC143C", health_direction=HealthDirection.HIGHER_BETTER),

    # ── 电气健康 ──
    MetricDef("current", "电流-A", "A", "电流",
              Dimension.ELECTRICAL, degradation_sensitive=True,
              chart_color="#FF7F0E", health_direction=HealthDirection.STABLE_BETTER),
    MetricDef("voltage", "电压-V", "V", "电压",
              Dimension.ELECTRICAL, degradation_sensitive=False,
              chart_color="#2CA02C", health_direction=HealthDirection.STABLE_BETTER),
    MetricDef("elec_power", "电功率-W", "W", "电功率",
              Dimension.ELECTRICAL, degradation_sensitive=True,
              chart_color="#D62728", health_direction=HealthDirection.LOWER_BETTER),
    MetricDef("drive_eff", "电驱效率-%", "%", "电驱效率",
              Dimension.ELECTRICAL, degradation_sensitive=True,
              chart_color="#9467BD", health_direction=HealthDirection.HIGHER_BETTER),

    # ── 机械健康 ──
    MetricDef("thrust", "拉力-g", "g", "拉力",
              Dimension.MECHANICAL, degradation_sensitive=True,
              chart_color="#1F77B4", health_direction=HealthDirection.HIGHER_BETTER),
    MetricDef("torque", "扭矩-N•m", "N·m", "扭矩",
              Dimension.MECHANICAL, degradation_sensitive=True,
              chart_color="#8C564B", health_direction=HealthDirection.STABLE_BETTER),
    MetricDef("rpm", "光电转速-RPM", "RPM", "转速",
              Dimension.MECHANICAL, degradation_sensitive=True,
              chart_color="#17BECF", health_direction=HealthDirection.STABLE_BETTER),
    MetricDef("shaft_power", "轴功率-W", "W", "轴功率",
              Dimension.MECHANICAL, degradation_sensitive=False,
              chart_color="#BCBD22", health_direction=HealthDirection.STABLE_BETTER),

    # ── 热特征 ──
    MetricDef("temp", "红外温度-℃", "℃", "红外温度",
              Dimension.THERMAL, degradation_sensitive=True,
              chart_color="#FF4500", health_direction=HealthDirection.LOWER_BETTER),

    # ── 能耗 ──
    MetricDef("wh", "耗电量(Wh)-Wh", "Wh", "累计能耗",
              Dimension.ENERGY, degradation_sensitive=True,
              chart_color="#7F7F7F", health_direction=HealthDirection.LOWER_BETTER),
    MetricDef("ah", "耗电量(Ah)-Ah", "Ah", "累计安时",
              Dimension.ENERGY, degradation_sensitive=False,
              chart_color="#B0B0B0", health_direction=HealthDirection.LOWER_BETTER),
]

# ═══════════════════════════════════════════════════════════════
# 特征注册 — 新增时域/频域特征只需加一行
# ═══════════════════════════════════════════════════════════════

FEATURE_REGISTRY: list[FeatureDef] = [
    # ── 时域特征 ──
    FeatureDef("rms", "RMS有效值", AnalysisType.TIME_DOMAIN, "",
               ["拉力-g", "电流-A", "扭矩-N•m"],
               HealthDirection.STABLE_BETTER),

    FeatureDef("std", "标准差", AnalysisType.TIME_DOMAIN, "",
               ["拉力-g", "电流-A", "扭矩-N•m", "光电转速-RPM"],
               HealthDirection.LOWER_BETTER),

    FeatureDef("cv", "变异系数(CV)", AnalysisType.TIME_DOMAIN, "%",
               ["拉力-g", "电流-A", "光电转速-RPM"],
               HealthDirection.LOWER_BETTER),

    FeatureDef("skewness", "偏度", AnalysisType.TIME_DOMAIN, "",
               ["拉力-g", "电流-A", "扭矩-N•m"],
               HealthDirection.STABLE_BETTER),

    FeatureDef("kurtosis", "峰度", AnalysisType.TIME_DOMAIN, "",
               ["拉力-g", "电流-A", "扭矩-N•m"],
               HealthDirection.LOWER_BETTER),

    FeatureDef("crest_factor", "波峰因子", AnalysisType.TIME_DOMAIN, "",
               ["拉力-g", "扭矩-N•m"],
               HealthDirection.LOWER_BETTER),

    FeatureDef("peak_to_peak", "峰峰值", AnalysisType.TIME_DOMAIN, "",
               ["拉力-g", "电流-A", "扭矩-N•m"],
               HealthDirection.LOWER_BETTER),

    FeatureDef("impulse_factor", "脉冲因子", AnalysisType.TIME_DOMAIN, "",
               ["拉力-g", "扭矩-N•m"],
               HealthDirection.STABLE_BETTER),

    # ── 频域特征 ──
    FeatureDef("spectral_centroid", "频谱重心", AnalysisType.FREQ_DOMAIN, "Hz",
               ["拉力-g", "电流-A", "扭矩-N•m"],
               HealthDirection.STABLE_BETTER),

    FeatureDef("spectral_spread", "频谱分散度", AnalysisType.FREQ_DOMAIN, "Hz",
               ["拉力-g", "电流-A", "扭矩-N•m"],
               HealthDirection.LOWER_BETTER),

    FeatureDef("spectral_skewness", "频谱偏度", AnalysisType.FREQ_DOMAIN, "",
               ["拉力-g", "扭矩-N•m"],
               HealthDirection.STABLE_BETTER),

    FeatureDef("spectral_kurtosis", "频谱峰度", AnalysisType.FREQ_DOMAIN, "",
               ["电流-A", "扭矩-N•m"],
               HealthDirection.LOWER_BETTER),

    FeatureDef("dominant_freq", "主频", AnalysisType.FREQ_DOMAIN, "Hz",
               ["拉力-g", "电流-A", "扭矩-N•m"],
               HealthDirection.STABLE_BETTER),

    FeatureDef("dominant_amp", "主频幅值", AnalysisType.FREQ_DOMAIN, "",
               ["拉力-g", "扭矩-N•m"],
               HealthDirection.LOWER_BETTER),

    FeatureDef("spectral_energy", "频谱总能量", AnalysisType.FREQ_DOMAIN, "",
               ["拉力-g", "电流-A", "扭矩-N•m"],
               HealthDirection.LOWER_BETTER),
]

# ═══════════════════════════════════════════════════════════════
# 退化分析配置
# ═══════════════════════════════════════════════════════════════

DEGRADATION_MIN_SAMPLES = 5

# ═══════════════════════════════════════════════════════════════
# 健康评分标准 — 满血(1.0) ↔ 报废(0.0) 线性映射
# 每个维度取退化率(slope_per_hour)，在 [failure, full_health] 区间线性插值
# ═══════════════════════════════════════════════════════════════

HEALTH_STANDARDS: dict[Dimension, dict] = {
    Dimension.FORCE_EFF: {
        "metric": "系统力效",
        "throttle": 40.0,
        "full_health": 0.0,          # 退化率 ≥ 0 = 满分
        "failure": -1.0,            # 退化率 ≤ -1.0 g/W/h = 报废
        "unit": "g/W/h",
        "description": "力效退化率",
    },
    Dimension.ELECTRICAL: {
        "metric": "电流",
        "throttle": 40.0,
        "full_health": 0.0,
        "failure": 0.5,
        "unit": "A/h",
        "description": "电流退化率",
    },
    Dimension.MECHANICAL: {
        "metric": "拉力",
        "throttle": 40.0,
        "full_health": 0.0,
        "failure": -10.0,
        "unit": "g/h",
        "description": "推力退化率",
    },
    Dimension.THERMAL: {
        "metric": "红外温度",
        "throttle": 40.0,
        "full_health": 0.0,
        "failure": 5.0,
        "unit": "C/h",
        "description": "温度退化率",
    },
    Dimension.ENERGY: {
        "metric": "累计能耗",
        "throttle": 40.0,
        "full_health": 0.0,
        "failure": 10.0,
        "unit": "Wh/h",
        "description": "能耗退化率",
    },
}

# 查询辅助

def get_metric_by_key(key: str) -> MetricDef | None:
    for m in ALL_METRICS:
        if m.key == key:
            return m
    return None


def get_metrics_by_dimension(dim: Dimension) -> list[MetricDef]:
    return [m for m in ALL_METRICS if m.dimension == dim]


def get_features_by_analysis_type(at: AnalysisType) -> list[FeatureDef]:
    return [f for f in FEATURE_REGISTRY if f.analysis_type == at]


def get_features_for_signal(signal: str) -> list[FeatureDef]:
    return [f for f in FEATURE_REGISTRY if signal in f.source_signals]
