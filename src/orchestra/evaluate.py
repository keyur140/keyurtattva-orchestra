# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Per-piece evaluation shared by the study runner and song mode."""
from __future__ import annotations

import math

import numpy as np

from .analysis import (detect_boundaries, dynamic_range_db, dynamics_accuracy, load_audio,
                       loudness_curve, boundary_f, random_boundary_f)
from .clap import ClapScorer, clap_available, presence_auc
from .conductor import boundaries, dynamics_curve
from .instruments import FAMILIES, FAMILY_LABELS
from .judge import CRITERIA


def _want(flag, available: bool, name: str, strict: bool, log) -> bool:
    if flag is False:
        return False
    if available:
        return True
    msg = f"{name} needs torch + transformers (pip install -r requirements-models.txt)"
    if flag is True and strict:
        raise RuntimeError(msg)
    log(f"[skip] {msg}")
    return False


class Evaluator:
    def __init__(self, metrics_cfg: dict, strict: bool, log=print):
        self.log = log
        self.tolerance = float(metrics_cfg.get("structure_tolerance_s", 2.0))
        clap_cfg = metrics_cfg.get("clap", {})
        judge_cfg = metrics_cfg.get("judge", {})
        clap_flag = clap_cfg.get("enabled", True) if isinstance(clap_cfg, dict) else clap_cfg
        judge_flag = judge_cfg.get("enabled", False) if isinstance(judge_cfg, dict) else judge_cfg
        clap_flag = None if clap_flag == "auto" else clap_flag
        judge_flag = None if judge_flag == "auto" else judge_flag
        self.clap = None
        self.judge = None
        if _want(clap_flag, clap_available(), "CLAP", strict, log):
            model_id = clap_cfg.get("model_id", "laion/larger_clap_music") if isinstance(clap_cfg, dict) else "laion/larger_clap_music"
            try:
                self.clap = ClapScorer(model_id)
            except Exception as e:  # e.g. no internet for the first download
                if strict:
                    raise
                log(f"[skip] CLAP could not load: {e}")
        if _want(judge_flag, clap_available(), "AI judge", strict, log):
            from .judge import AudioJudge
            model_id = judge_cfg.get("model_id", "Qwen/Qwen2-Audio-7B-Instruct") if isinstance(judge_cfg, dict) else "Qwen/Qwen2-Audio-7B-Instruct"
            try:
                self.judge = AudioJudge(model_id)
            except Exception as e:
                if strict:
                    raise
                log(f"[skip] AI judge could not load: {e}")

    def info(self) -> dict:
        return {"clap": self.clap.info() if self.clap else None,
                "judge": self.judge.info() if self.judge else None,
                "structure_tolerance_s": self.tolerance}

    def evaluate(self, audio_path, request_text: str, target_sections, target_families: list[str],
                 duration: float, culture_text: str | None = None):
        y = load_audio(audio_path)
        measured = loudness_curve(y)
        planned = dynamics_curve(target_sections, duration)
        ref_bounds = boundaries(target_sections)
        est = detect_boundaries(y, k=len(target_sections))
        out = {
            "duration_s": round(len(y) / 22050, 3),
            "dynamics_accuracy": dynamics_accuracy(measured, planned),
            "dynamic_range_db": dynamic_range_db(measured),
            "structure_f": boundary_f(est, ref_bounds, self.tolerance),
            "structure_chance": random_boundary_f(ref_bounds, duration, self.tolerance, trials=200),
            "est_boundaries": [round(b, 2) for b in est],
        }
        emb = None
        if self.clap:
            emb = self.clap.embed_audio_file(audio_path)
            out["prompt_adherence"] = self.clap.similarity(emb, request_text)
            for fam in FAMILIES:
                out[f"fam_{fam}"] = self.clap.similarity(emb, FAMILY_LABELS[fam])
            out["section_clarity_raw"] = presence_auc({f: out[f"fam_{f}"] for f in FAMILIES}, target_families)
            out["cultural_similarity"] = self.clap.similarity(emb, culture_text) if culture_text else math.nan
        if self.judge:
            j = self.judge.judge(audio_path, request_text)
            for c in CRITERIA:
                out[f"judge_{c}"] = j[c]
            out["judge_advice"] = j.get("advice", "")
            out["judge_raw"] = j.get("raw", "")
        return out, emb


def calibrated_clarity(pieces, target_families_by_request: dict[str, list[str]]):
    """Section clarity with per-generator z-scored family similarities (removes label bias)."""
    cols = [f"fam_{f}" for f in FAMILIES]
    if not all(c in pieces for c in cols):
        return pieces
    pieces = pieces.copy()
    z = pieces.groupby("generator")[cols].transform(lambda s: (s - s.mean()) / (s.std(ddof=0) + 1e-9))
    pieces["section_clarity"] = [
        presence_auc({f: z.loc[i, f"fam_{f}"] for f in FAMILIES}, target_families_by_request[r])
        for i, r in zip(pieces.index, pieces["request_id"])]
    return pieces


def composite(row: dict) -> float:
    """Heuristic 0-1 score used only to pick the best song version (never in hypothesis tests)."""
    parts = []
    pa = row.get("prompt_adherence")
    if pa is not None and np.isfinite(pa):
        parts.append(min(1.0, max(0.0, pa / 0.6)))
    for key, fn in (("section_clarity_raw", lambda v: v), ("dynamics_accuracy", lambda v: (v + 1) / 2),
                    ("structure_f", lambda v: v), ("judge_overall", lambda v: v / 10)):
        v = row.get(key)
        if v is not None and np.isfinite(v):
            parts.append(fn(v))
    return float(np.mean(parts)) if parts else math.nan
