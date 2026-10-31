# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Open text-to-audio generators: MusicGen (Meta) and Stable Audio Open (Stability AI).

Both are loaded through Hugging Face libraries. Model weights are downloaded on first use.
Stable Audio Open is a gated model: accept its licence on Hugging Face and put your token
in ``.env`` as ``HF_TOKEN``. Check each model card for its licence before any reuse
(MusicGen weights are released for non-commercial use).
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np


def _torch():
    import torch
    return torch


def _device(pref: str = "auto") -> str:
    torch = _torch()
    if pref != "auto":
        return pref
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _write(out_wav: Path, audio: np.ndarray, sr: int) -> None:
    import soundfile as sf
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim == 2 and audio.shape[0] in (1, 2) and audio.shape[0] < audio.shape[1]:
        audio = audio.T
    sf.write(str(out_wav), audio, sr, subtype="PCM_16")


def _revision(model) -> str | None:
    return getattr(getattr(model, "config", None), "_commit_hash", None)


class MusicGenGenerator:
    name = "musicgen"
    conditions = ("plain", "expert", "pipeline")
    reproducible = True

    def __init__(self, model_id: str = "facebook/musicgen-medium", device: str = "auto",
                 guidance_scale: float = 3.0, max_prompt_words: int = 90):
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
        self.model_id = model_id
        self.device = _device(device)
        self.guidance_scale = guidance_scale
        self.max_prompt_words = max_prompt_words
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = MusicgenForConditionalGeneration.from_pretrained(model_id).to(self.device)
        self.model.eval()
        self.sr = self.model.config.audio_encoder.sampling_rate
        self.frame_rate = self.model.config.audio_encoder.frame_rate

    def info(self) -> dict:
        return {"generator": self.name, "model": self.model_id, "revision": _revision(self.model),
                "device": self.device, "guidance_scale": self.guidance_scale, "sample_rate": self.sr}

    def generate(self, *, condition, prompt, seed, duration, out_wav, **_) -> dict:
        torch = _torch()
        torch.manual_seed(seed)
        np.random.seed(seed)
        inputs = self.processor(text=[prompt], padding=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            audio = self.model.generate(**inputs, do_sample=True, guidance_scale=self.guidance_scale,
                                        max_new_tokens=int(duration * self.frame_rate))
        _write(Path(out_wav), audio[0].float().cpu().numpy(), self.sr)
        return self.info()


class MusicGenMelodyGenerator(MusicGenGenerator):
    """MusicGen-melody: the text prompt AND your voice note (its tune) condition the audio.

    Weights are licensed for non-commercial use, so publish mode blocks this generator."""
    name = "musicgen_melody"
    conditions = ("pipeline",)

    def __init__(self, model_id: str = "facebook/musicgen-melody", device: str = "auto",
                 guidance_scale: float = 3.0, max_prompt_words: int = 90):
        from transformers import AutoProcessor, MusicgenMelodyForConditionalGeneration
        self.model_id = model_id
        self.device = _device(device)
        self.guidance_scale = guidance_scale
        self.max_prompt_words = max_prompt_words
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = MusicgenMelodyForConditionalGeneration.from_pretrained(model_id).to(self.device)
        self.model.eval()
        self.sr = self.model.config.audio_encoder.sampling_rate
        self.frame_rate = self.model.config.audio_encoder.frame_rate

    def generate(self, *, condition, prompt, seed, duration, out_wav, voice_path=None, **_) -> dict:
        torch = _torch()
        torch.manual_seed(seed)
        np.random.seed(seed)
        kwargs = {"text": [prompt], "padding": True, "return_tensors": "pt"}
        if voice_path:
            import librosa
            y, _ = librosa.load(str(voice_path), sr=self.processor.sampling_rate, mono=True)
            kwargs.update(audio=[y], sampling_rate=self.processor.sampling_rate)
        inputs = self.processor(**kwargs).to(self.device)
        with torch.no_grad():
            audio = self.model.generate(**inputs, do_sample=True, guidance_scale=self.guidance_scale,
                                        max_new_tokens=int(duration * self.frame_rate))
        _write(Path(out_wav), audio[0].float().cpu().numpy(), self.sr)
        info = self.info()
        info["voice_conditioned"] = bool(voice_path)
        return info


class StableAudioGenerator:
    name = "stable_audio"
    conditions = ("plain", "expert", "pipeline")
    reproducible = True

    def __init__(self, model_id: str = "stabilityai/stable-audio-open-1.0", device: str = "auto",
                 steps: int = 100, guidance_scale: float = 7.0, max_prompt_words: int = 60):
        from diffusers import StableAudioPipeline
        torch = _torch()
        self.model_id = model_id
        self.device = _device(device)
        self.steps = steps
        self.guidance_scale = guidance_scale
        self.max_prompt_words = max_prompt_words
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.pipe = StableAudioPipeline.from_pretrained(model_id, torch_dtype=dtype,
                                                        token=os.environ.get("HF_TOKEN") or None)
        self.pipe = self.pipe.to(self.device)
        self.sr = self.pipe.vae.sampling_rate

    def info(self) -> dict:
        return {"generator": self.name, "model": self.model_id, "device": self.device,
                "steps": self.steps, "guidance_scale": self.guidance_scale, "sample_rate": self.sr}

    def generate(self, *, condition, prompt, seed, duration, out_wav, **_) -> dict:
        torch = _torch()
        gen = torch.Generator(self.device if self.device != "mps" else "cpu").manual_seed(seed)
        result = self.pipe(prompt, negative_prompt="low quality, distorted, noise",
                           num_inference_steps=self.steps, guidance_scale=self.guidance_scale,
                           audio_end_in_s=float(min(duration, 47.0)), num_waveforms_per_prompt=1,
                           generator=gen)
        _write(Path(out_wav), result.audios[0].T.float().cpu().numpy(), self.sr)
        return self.info()
