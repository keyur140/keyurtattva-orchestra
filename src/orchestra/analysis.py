# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Signal-level metrics that need no neural model: dynamics accuracy, structure, range."""
from __future__ import annotations

import math

import numpy as np

ANALYSIS_SR = 22050


def load_audio(path, sr: int = ANALYSIS_SR) -> np.ndarray:
    import librosa
    y, _ = librosa.load(str(path), sr=sr, mono=True)
    return y


def loudness_curve(y: np.ndarray, sr: int = ANALYSIS_SR, hop_s: float = 1.0) -> np.ndarray:
    """RMS level in dBFS per non-overlapping window of ``hop_s`` seconds."""
    n = int(sr * hop_s)
    frames = len(y) // n
    if frames == 0:
        return np.array([])
    blocks = y[: frames * n].reshape(frames, n)
    rms = np.sqrt(np.mean(blocks ** 2, axis=1))
    return 20 * np.log10(rms + 1e-9)


def dynamics_accuracy(measured_db: np.ndarray, planned_db: np.ndarray) -> float:
    """Spearman correlation between measured and planned loudness over time.

    Undefined (NaN) when the plan is flat or the audio is silent, because a rank
    correlation needs variation in both series.
    """
    from scipy.stats import spearmanr
    m = min(len(measured_db), len(planned_db))
    if m < 4:
        return math.nan
    a, b = measured_db[:m], planned_db[:m]
    if np.ptp(b) < 1e-6 or np.ptp(a) < 1e-6 or np.max(a) < -80:
        return math.nan
    rho = spearmanr(a, b).statistic
    return float(rho) if np.isfinite(rho) else math.nan


def dynamic_range_db(measured_db: np.ndarray) -> float:
    audible = measured_db[measured_db > -80]
    if len(audible) < 2:
        return math.nan
    return float(np.percentile(audible, 95) - np.percentile(audible, 5))


def detect_boundaries(y: np.ndarray, k: int, sr: int = ANALYSIS_SR, frame_s: float = 0.5) -> list[float]:
    """Inner boundaries (s) from agglomerative segmentation of timbre + harmony features."""
    import librosa
    if k < 2 or len(y) < sr * 2:
        return []
    hop = 512
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop)
    rms = librosa.feature.rms(y=y, hop_length=hop)
    feats = np.vstack([mfcc, chroma, librosa.amplitude_to_db(rms + 1e-9)])
    step = max(1, int(frame_s * sr / hop))
    n = feats.shape[1] // step
    if n < k:
        return []
    pooled = feats[:, : n * step].reshape(feats.shape[0], n, step).mean(axis=2)
    pooled = (pooled - pooled.mean(axis=1, keepdims=True)) / (pooled.std(axis=1, keepdims=True) + 1e-9)
    bounds = librosa.segment.agglomerative(pooled, k)
    return [float(b * step * hop / sr) for b in bounds if b > 0]


def boundary_f(estimated: list[float], reference: list[float], tolerance: float = 2.0) -> float:
    """Boundary-detection F-measure with one-to-one matching inside +/- tolerance seconds."""
    if not reference:
        return math.nan
    if not estimated:
        return 0.0
    pairs = sorted((abs(e - r), i, j) for i, e in enumerate(estimated) for j, r in enumerate(reference)
                   if abs(e - r) <= tolerance)
    used_e, used_r, hits = set(), set(), 0
    for _, i, j in pairs:
        if i not in used_e and j not in used_r:
            used_e.add(i)
            used_r.add(j)
            hits += 1
    if hits == 0:
        return 0.0
    p, r = hits / len(estimated), hits / len(reference)
    return 2 * p * r / (p + r)


def random_boundary_f(reference: list[float], duration: float, tolerance: float = 2.0,
                      trials: int = 1000, seed: int = 0) -> float:
    """Chance level for boundary_f: random boundaries, same count as the reference."""
    if not reference:
        return math.nan
    rng = np.random.default_rng(seed)
    scores = [boundary_f(sorted(rng.uniform(0, duration, len(reference)).tolist()), reference, tolerance)
              for _ in range(trials)]
    return float(np.mean(scores))
