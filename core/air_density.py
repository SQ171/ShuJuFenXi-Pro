"""空气密度计算与力效大气修正"""

import numpy as np
from core.constants import (
    STD_TEMP_C, STD_PRESSURE_HPA, STD_RH_PCT, R_DRY_AIR, R_VAPOR,
)


def air_density(temp_c: float, pressure_hpa: float, rh_pct: float) -> float:
    """计算实际空气密度 (kg/m³)

    Args:
        temp_c: 温度 °C
        pressure_hpa: 大气压 hPa
        rh_pct: 相对湿度 %
    """
    T = temp_c + 273.15                 # K
    p = pressure_hpa * 100              # Pa

    # 饱和水汽压 (Tetens公式) [hPa]
    e_sat = 6.1078 * np.exp(17.27 * temp_c / (temp_c + 237.3))
    e = e_sat * (rh_pct / 100.0) * 100  # 实际水汽压 [Pa]

    p_d = p - e                          # 干空气分压 [Pa]

    rho = p_d / (R_DRY_AIR * T) + e / (R_VAPOR * T)
    return float(rho)


def standard_air_density() -> float:
    """标准空气密度 (kg/m³)"""
    return air_density(STD_TEMP_C, STD_PRESSURE_HPA, STD_RH_PCT)


def correction_factor(temp_c: float, pressure_hpa: float, rh_pct: float) -> float:
    """等效因子 = sqrt(ρ_标准 / ρ_实际)

    推力 ∝ ρ，功率 ∝ ρ，力效 = 推力/功率 ≈ 常数 w.r.t. ρ
    取平方根作为折中修正，避免对力效过度修正
    """
    import numpy as np
    rho_actual = air_density(temp_c, pressure_hpa, rh_pct)
    rho_std = standard_air_density()
    if rho_actual <= 0:
        return 1.0
    return float(np.sqrt(rho_std / rho_actual))


def parse_env_from_metadata(metadata: dict) -> tuple[float, float, float]:
    """从 CSV 元数据提取温度/气压/湿度，转换单位

    注意: CSV 中大气压单位是 kPa，需转为 hPa
    """
    temp_c = float(metadata.get("环境温度", STD_TEMP_C))
    pressure_kpa = float(metadata.get("大气压", STD_PRESSURE_HPA / 10))
    pressure_hpa = pressure_kpa * 10.0  # kPa → hPa
    rh_pct = float(metadata.get("环境湿度", STD_RH_PCT))
    return temp_c, pressure_hpa, rh_pct
