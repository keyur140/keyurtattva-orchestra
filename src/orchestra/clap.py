# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""CLAP text-audio embeddings (LAION CLAP, open weights) for prompt adherence, family
detection, cultural similarity and Frechet Audio Distance."""
from __future__ import annotations

import math

import numpy as np

CLAP_SR = 48000
WINDOW_S = 10.0


def clap_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


class ClapScorer:
    def __init__(self, model_id: str = "laion/larger_clap_music", device: str = "auto"):
        import torch
        from transformers import ClapModel, ClapProcessor
        self.torch = torch
        self.model_id = model_id
        self.device = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
        self.processor = ClapProcessor.from_pretrained(model_id)
        self.model = ClapModel.from_pretrained(model_id).to(self.device).eval()
        self._text_cache: dict[str, np.ndarray] = {}

    def info(self) -> dict:
        return {"model": self.model_id, "revision": getattr(self.model.config, "_commit_hash", None),
                "device": self.device, "window_s": WINDOW_S}

    def _audio_inputs(self, chunks: list[np.ndarray]):
        try:
            return self.processor(audios=chunks, sampling_rate=CLAP_SR, return_tensors="pt")
        except TypeError:
            return self.processor(audio=chunks, sampling_rate=CLAP_SR, return_tensors="pt")

    def _tensor(self, out, name: str):
        """Newer transformers versions may return an output object instead of a tensor."""
        if isinstance(out, self.torch.Tensor):
            return out
        for attr in (name, "pooler_output"):
            v = getattr(out, attr, None)
            if isinstance(v, self.torch.Tensor):
                return v
        return out[0]

    def embed_audio_file(self, path) -> np.ndarray:
        """Mean of L2-normalised embeddings of consecutive 10 s windows, re-normalised."""
        import librosa
        y, _ = librosa.load(str(path), sr=CLAP_SR, mono=True)
        n = int(WINDOW_S * CLAP_SR)
        chunks = [y[i:i + n] for i in range(0, max(len(y) - n // 2, 1), n)] or [y]
        chunks = [c for c in chunks if len(c) > CLAP_SR] or [y]
        inputs = self._audio_inputs(chunks)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with self.torch.no_grad():
            emb = self._tensor(self.model.get_audio_features(**inputs), "audio_embeds")
        emb = emb.float().cpu().numpy()
        emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12
        mean = emb.mean(axis=0)
        return mean / (np.linalg.norm(mean) + 1e-12)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        missing = [t for t in texts if t not in self._text_cache]
        if missing:
            inputs = self.processor(text=missing, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with self.torch.no_grad():
                emb = self._tensor(self.model.get_text_features(**inputs), "text_embeds").float().cpu().numpy()
            emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12
            for t, e in zip(missing, emb):
                self._text_cache[t] = e
        return np.stack([self._text_cache[t] for t in texts])

    def similarity(self, audio_emb: np.ndarray, text: str) -> float:
        return float(audio_emb @ self.embed_texts([text])[0])


def presence_auc(scores: dict[str, float], requested: list[str]) -> float:
    """Probability that a requested family scores above a non-requested one (ties count 0.5)."""
    pos = [v for k, v in scores.items() if k in requested and np.isfinite(v)]
    neg = [v for k, v in scores.items() if k not in requested and np.isfinite(v)]
    if not pos or not neg:
        return math.nan
    wins = sum(1.0 if p > q else 0.5 if p == q else 0.0 for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def frechet_distance(a: np.ndarray, b: np.ndarray, eps: float = 1e-6) -> float:
    """Frechet distance between Gaussian fits of two embedding sets (FAD)."""
    from scipy import linalg
    if len(a) < 2 or len(b) < 2:
        return math.nan
    mu1, mu2 = a.mean(0), b.mean(0)
    s1 = np.cov(a, rowvar=False) + eps * np.eye(a.shape[1])
    s2 = np.cov(b, rowvar=False) + eps * np.eye(b.shape[1])
    covmean = linalg.sqrtm(s1 @ s2)
    if isinstance(covmean, tuple):  # older SciPy returns (value, error)
        covmean = covmean[0]
    covmean = np.real(covmean)
    return float(np.sum((mu1 - mu2) ** 2) + np.trace(s1 + s2 - 2 * covmean))
