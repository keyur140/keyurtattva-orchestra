# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Preregistered statistics: paired Wilcoxon signed-rank tests, Holm correction,
matched-pairs rank-biserial effect sizes, bootstrap confidence intervals, and
Spearman agreement between measures."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

CONFIRMATORY_METRICS = ["prompt_adherence", "section_clarity", "dynamics_accuracy", "structure_f"]
SECONDARY_METRICS = ["judge_overall", "cultural_similarity", "dynamic_range_db"]


def rank_biserial(diffs: np.ndarray) -> float:
    d = diffs[diffs != 0]
    if len(d) == 0:
        return 0.0
    ranks = pd.Series(np.abs(d)).rank().to_numpy()
    w_pos, w_neg = ranks[d > 0].sum(), ranks[d < 0].sum()
    return float((w_pos - w_neg) / (w_pos + w_neg))


def bootstrap_ci(diffs: np.ndarray, n_boot: int, seed: int, stat=np.median, level: float = 0.95):
    if len(diffs) < 2:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diffs), size=(n_boot, len(diffs)))
    boots = stat(diffs[idx], axis=1)
    lo, hi = np.percentile(boots, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return float(lo), float(hi)


def holm(pvalues: list[float]) -> list[float]:
    p = np.array(pvalues, dtype=float)
    out = np.full(len(p), np.nan)
    ok = np.where(np.isfinite(p))[0]
    order = ok[np.argsort(p[ok])]
    m = len(order)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        out[i] = running
    return out.tolist()


def paired_test(df: pd.DataFrame, metric: str, a: str, b: str, n_boot: int, seed: int) -> dict:
    """Compare condition ``a`` against ``b`` on ``metric``; ``df`` holds one row per request."""
    from scipy.stats import wilcoxon
    wide = df.pivot_table(index="request_id", columns="condition", values=metric, aggfunc="mean")
    if a not in wide or b not in wide:
        return {}
    pair = wide[[a, b]].dropna()
    diffs = (pair[a] - pair[b]).to_numpy()
    res = {"metric": metric, "comparison": f"{a} vs {b}", "n_pairs": len(diffs),
           "median_a": float(pair[a].median()) if len(pair) else math.nan,
           "median_b": float(pair[b].median()) if len(pair) else math.nan,
           "median_diff": float(np.median(diffs)) if len(diffs) else math.nan}
    if len(diffs) >= 6 and np.any(diffs != 0):
        test = wilcoxon(diffs, zero_method="wilcox", alternative="two-sided")
        res["W"] = float(test.statistic)
        res["p"] = float(test.pvalue)
    else:
        res["W"], res["p"] = math.nan, math.nan
    res["rank_biserial"] = rank_biserial(diffs) if len(diffs) else math.nan
    res["ci95_low"], res["ci95_high"] = bootstrap_ci(diffs, n_boot, seed)
    return res


def run_tests(per_request: pd.DataFrame, comparisons: list[tuple[str, str]], metrics: list[str],
              family: str, n_boot: int, seed: int, alpha: float) -> pd.DataFrame:
    rows = []
    for gen, sub in per_request.groupby("generator"):
        for a, b in comparisons:
            for m in metrics:
                if m not in sub:
                    continue
                r = paired_test(sub, m, a, b, n_boot, seed)
                if r:
                    r["generator"] = gen
                    r["family"] = family
                    rows.append(r)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["p_holm"] = holm(out["p"].tolist())
    out["significant"] = [bool(p < alpha) if np.isfinite(p) else None for p in out["p_holm"]]
    cols = ["family", "generator", "comparison", "metric", "n_pairs", "median_a", "median_b", "median_diff",
            "ci95_low", "ci95_high", "W", "p", "p_holm", "significant", "rank_biserial"]
    return out[cols]


def agreement(pieces: pd.DataFrame, measures: list[str]) -> pd.DataFrame:
    """Spearman correlation between every pair of measures across all pieces."""
    from scipy.stats import spearmanr
    rows = []
    cols = [m for m in measures if m in pieces and pieces[m].notna().sum() >= 5]
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            pair = pieces[[a, b]].dropna()
            if len(pair) < 5 or pair[a].nunique() < 2 or pair[b].nunique() < 2:
                continue
            r = spearmanr(pair[a], pair[b])
            rows.append({"measure_a": a, "measure_b": b, "n": len(pair), "spearman_rho": float(r.statistic),
                         "p": float(r.pvalue)})
    return pd.DataFrame(rows)
