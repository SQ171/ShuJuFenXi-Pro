"""Pipeline S5: 时域特征 + 频域特征提取"""

import numpy as np
import pandas as pd
from analysis.pipeline import AnalysisContext
from core.models import FeatureResult
from core.constants import (
    COL_STEP_ID, COL_NOMINAL_THROTTLE, COL_CYCLE_NUM,
    COL_SOURCE_FILE, COL_IS_STABILIZING, COL_CUMULATIVE_RUNTIME,
    SAMPLING_RATE_HZ,
)
from config import FEATURE_REGISTRY


def extract_features(ctx: AnalysisContext) -> AnalysisContext:
    df = ctx.unified_df
    if df is None or df.empty:
        return ctx

    results = []
    for (source_file, cycle_num, step_id), group in df.groupby(
        [COL_SOURCE_FILE, COL_CYCLE_NUM, COL_STEP_ID], sort=True
    ):
        stable = group[~group[COL_IS_STABILIZING]]
        if len(stable) < 10:
            continue

        nominal_throttle = group[COL_NOMINAL_THROTTLE].mode()
        if len(nominal_throttle) == 0:
            continue
        nominal_throttle = float(nominal_throttle.iloc[0])
        cum_runtime = group[COL_CUMULATIVE_RUNTIME].mean()

        for feat_def in FEATURE_REGISTRY:
            for signal in feat_def.source_signals:
                if signal not in stable.columns:
                    continue
                signal_values = stable[signal].dropna().values
                if len(signal_values) < 10:
                    continue

                value = _compute_feature(feat_def.key, signal_values)
                if value is not None and not np.isnan(value):
                    results.append(FeatureResult(
                        step_id=int(step_id),
                        nominal_throttle=nominal_throttle,
                        cycle_num=int(cycle_num),
                        source_file=source_file,
                        source_signal=signal,
                        feature_key=feat_def.key,
                        feature_value=float(value),
                        cumulative_runtime=float(cum_runtime),
                    ))

    ctx.feature_results = results
    return ctx


# ═══════════════════════════════════════════════════════════════
# 时域特征计算
# ═══════════════════════════════════════════════════════════════

def _compute_feature(key: str, signal: np.ndarray) -> float | None:
    s = signal - np.mean(signal) if key not in ("rms", "std", "peak_to_peak") else signal

    if key == "rms":
        return float(np.sqrt(np.mean(s ** 2)))
    elif key == "std":
        return float(np.std(s))
    elif key == "cv":
        mean_val = np.mean(np.abs(signal))
        return float(np.std(signal) / mean_val * 100) if mean_val != 0 else None
    elif key == "skewness":
        return _skewness(s)
    elif key == "kurtosis":
        return _kurtosis(s)
    elif key == "crest_factor":
        rms = np.sqrt(np.mean(s ** 2))
        return float(np.max(np.abs(s)) / rms) if rms > 0 else None
    elif key == "peak_to_peak":
        return float(np.max(s) - np.min(s))
    elif key == "impulse_factor":
        mean_abs = np.mean(np.abs(s))
        return float(np.max(np.abs(s)) / mean_abs) if mean_abs > 0 else None
    elif key in _FREQ_FUNCS:
        freqs, mags = _compute_spectrum(s)
        return _FREQ_FUNCS[key](freqs, mags)
    return None


# ═══════════════════════════════════════════════════════════════
# 频域特征计算
# ═══════════════════════════════════════════════════════════════

def _compute_spectrum(signal: np.ndarray, fs: float = SAMPLING_RATE_HZ) -> tuple:
    n = len(signal)
    if n < 4:
        return np.array([0]), np.array([0])
    fft_vals = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    return freqs, fft_vals


def _spectral_centroid(freqs: np.ndarray, mags: np.ndarray) -> float:
    total = np.sum(mags)
    return float(np.sum(freqs * mags) / total) if total > 0 else 0.0


def _spectral_spread(freqs: np.ndarray, mags: np.ndarray) -> float:
    centroid = _spectral_centroid(freqs, mags)
    total = np.sum(mags)
    return float(np.sqrt(np.sum(((freqs - centroid) ** 2) * mags) / total)) if total > 0 else 0.0


def _spectral_skewness(freqs: np.ndarray, mags: np.ndarray) -> float:
    centroid = _spectral_centroid(freqs, mags)
    spread = _spectral_spread(freqs, mags)
    if spread == 0:
        return 0.0
    total = np.sum(mags)
    return float(np.sum(((freqs - centroid) / spread) ** 3 * mags) / total) if total > 0 else 0.0


def _spectral_kurtosis(freqs: np.ndarray, mags: np.ndarray) -> float:
    centroid = _spectral_centroid(freqs, mags)
    spread = _spectral_spread(freqs, mags)
    if spread == 0:
        return 0.0
    total = np.sum(mags)
    return float(np.sum(((freqs - centroid) / spread) ** 4 * mags) / total) if total > 0 else 0.0


def _dominant_freq(freqs: np.ndarray, mags: np.ndarray) -> float:
    # 跳过DC分量(freq=0)
    mask = freqs > 0
    if not np.any(mask):
        return 0.0
    idx = np.argmax(mags[mask])
    return float(freqs[mask][idx])


def _dominant_amp(freqs: np.ndarray, mags: np.ndarray) -> float:
    mask = freqs > 0
    if not np.any(mask):
        return float(mags[0]) if len(mags) > 0 else 0.0
    return float(np.max(mags[mask]))


def _spectral_energy(freqs: np.ndarray, mags: np.ndarray) -> float:
    return float(np.sum(mags ** 2))


_FREQ_FUNCS = {
    "spectral_centroid": _spectral_centroid,
    "spectral_spread": _spectral_spread,
    "spectral_skewness": _spectral_skewness,
    "spectral_kurtosis": _spectral_kurtosis,
    "dominant_freq": _dominant_freq,
    "dominant_amp": _dominant_amp,
    "spectral_energy": _spectral_energy,
}


# ═══════════════════════════════════════════════════════════════
# 时域高阶统计量
# ═══════════════════════════════════════════════════════════════

def _skewness(x: np.ndarray) -> float:
    n = len(x)
    if n < 3:
        return 0.0
    m2 = np.mean(x ** 2)
    m3 = np.mean(x ** 3)
    return float(m3 / (m2 ** 1.5)) if m2 > 0 else 0.0


def _kurtosis(x: np.ndarray) -> float:
    n = len(x)
    if n < 4:
        return 0.0
    m2 = np.mean(x ** 2)
    m4 = np.mean(x ** 4)
    return float(m4 / (m2 ** 2)) - 3.0 if m2 > 0 else 0.0  # excess kurtosis
