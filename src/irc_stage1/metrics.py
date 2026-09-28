"""Illustrative candidate estimators. Settings are NOT preregistered defaults."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt, hilbert, welch


def _check(x: np.ndarray, sfreq: float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[0] < 3 or x.shape[1] < 50:
        raise ValueError("At least three channels and fifty samples required")
    if sfreq <= 0 or not np.isfinite(x).all():
        raise ValueError("Finite EEG samples and positive sampling frequency required")
    return x - x.mean(axis=1, keepdims=True)


def phase_connectivity(x: np.ndarray, sfreq: float, low: float, high: float) -> np.ndarray:
    """Debiased squared wPLI candidate; negative finite-sample values clipped to 0.

    Formula: ((ΣI)^2-ΣI²)/((Σ|I|)^2-ΣI²), I=Im(analytic_i*conj(analytic_j)).
    Single-epoch sample formulation, not a substitute for an agreed estimator.
    """
    x = _check(x, sfreq)
    if not (0 < low < high < sfreq / 2):
        raise ValueError("Band must lie inside Nyquist")
    sos = butter(4, [low, high], btype="bandpass", fs=sfreq, output="sos")
    z = hilbert(sosfiltfilt(sos, x, axis=1), axis=1)
    n = x.shape[0]
    result = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            im = np.imag(z[i] * z[j].conj())
            squared = np.square(im).sum()
            denominator = np.abs(im).sum() ** 2 - squared
            numerator = im.sum() ** 2 - squared
            value = max(0.0, numerator / denominator) if denominator > 1e-12 else 0.0
            result[i, j] = result[j, i] = min(value, 1.0)
    return result


def _design(x: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray]:
    if lag < 1 or x.shape[1] < max(50, (x.shape[0] * lag + 1) * 8):
        raise ValueError("Insufficient samples for requested VAR lag")
    target = x[:, lag:].T
    history = np.concatenate([x[:, lag - step:-step] for step in range(1, lag + 1)], axis=0).T
    return target, history


def fit_var(x: np.ndarray, sfreq: float, lag: int = 1) -> tuple[np.ndarray, float]:
    """OLS VAR and largest companion eigenvalue magnitude (not a Lyapunov exponent)."""
    x = _check(x, sfreq)
    target, history = _design(x, lag)
    coef = np.linalg.lstsq(history, target, rcond=None)[0].T
    n = x.shape[0]
    companion = np.zeros((n * lag, n * lag))
    companion[:n, :] = coef
    if lag > 1:
        companion[n:, :-n] = np.eye(n * (lag - 1))
    radius = float(max(abs(np.linalg.eigvals(companion))))
    return coef, radius


def directed_granger(x: np.ndarray, sfreq: float, lag: int = 1) -> np.ndarray:
    """Pairwise candidate log variance ratio; entry [source, target].

    No conditioning on other channels; not an inference of physiological causality.
    """
    x = _check(x, sfreq)
    n = x.shape[0]
    out = np.zeros((n, n))
    for source in range(n):
        for target in range(n):
            if source == target:
                continue
            y, self_lags = _design(x[target:target + 1], lag)
            _, source_lags = _design(x[source:source + 1], lag)
            reduced = y - self_lags @ np.linalg.lstsq(self_lags, y, rcond=None)[0]
            full = np.concatenate([self_lags, source_lags], axis=1)
            residual = y - full @ np.linalg.lstsq(full, y, rcond=None)[0]
            vr, vf = np.mean(reduced ** 2), np.mean(residual ** 2)
            out[source, target] = max(0.0, float(np.log(vr / vf))) if vf > 1e-15 else 0.0
    return out


def participation_ratio(x: np.ndarray, sfreq: float) -> float:
    x = _check(x, sfreq)
    values = np.linalg.eigvalsh(np.cov(x))
    values = np.maximum(values, 0)
    return float(values.sum() ** 2 / np.square(values).sum()) if np.any(values) else 0.0


def pca_error_slope(x: np.ndarray, sfreq: float) -> float:
    """Candidate mean finite difference of normalized PCA reconstruction errors.

    Calculated over ranks 1..n-1; telescopes, so this particular slope needs
    scientific review before any use as a μ proxy.
    """
    x = _check(x, sfreq)
    values = np.linalg.eigvalsh(np.cov(x))[::-1].clip(min=0)
    if values.sum() <= 0:
        return 0.0
    errors = 1 - np.cumsum(values[:-1]) / values.sum()
    return float(np.polyfit(np.arange(1, len(errors) + 1), errors, 1)[0]) if len(errors) > 1 else 0.0


def bandpowers(x: np.ndarray, sfreq: float, low: float = 8, high: float = 12) -> tuple[float, float]:
    x = _check(x, sfreq)
    f, p = welch(x, fs=sfreq, nperseg=min(x.shape[1], int(sfreq * 2)), axis=1)
    if not (0 <= low < high <= sfreq / 2):
        raise ValueError("Invalid band")
    total = float(np.trapezoid(p, f, axis=1).mean())
    use = (f >= low) & (f <= high)
    alpha = float(np.trapezoid(p[:, use], f[use], axis=1).mean()) if use.sum() > 1 else float("nan")
    return total, alpha


def summarize(x: np.ndarray, sfreq: float, band: tuple[float, float], lag: int = 1) -> dict:
    phase = phase_connectivity(x, sfreq, *band)
    directed = directed_granger(x, sfreq, lag)
    _, radius = fit_var(x, sfreq, lag)
    off_diag = ~np.eye(phase.shape[0], dtype=bool)
    total, alpha = bandpowers(x, sfreq)
    return {"rho_phase_mean": float(phase[off_diag].mean()),
            "rho_granger_mean": float(directed[off_diag].mean()),
            "gamma_var_spectral_radius": radius,
            "mu_participation_ratio": participation_ratio(x, sfreq),
            "mu_pca_error_slope": pca_error_slope(x, sfreq),
            "total_power": total, "alpha_power": alpha}
