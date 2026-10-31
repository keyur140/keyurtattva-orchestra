# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""AI audio judge: an open audio-language model rates each piece on a fixed rubric.

The judge hears the audio and reads the user's original request (never the compiled
prompt, so it cannot reward prompt wording). Decoding is greedy, so the same audio gets
the same rating. The judge is a secondary measure; its known biases are reported.
"""
from __future__ import annotations

import json
import math
import re

CRITERIA = ("adherence", "orchestration", "dynamics", "structure", "overall")

RUBRIC = """You are an expert orchestrator and music critic. Listen to the audio. It was generated for this request:
"{request}"
Rate it on each criterion from 1 (very poor) to 10 (excellent):
- adherence: how well it matches the request
- orchestration: the requested instruments are clearly audible and sound realistic
- dynamics: the loudness shape over time fits the request
- structure: clear sections and musical development
- overall: overall musical quality
Then give one short piece of advice to improve it.
Reply with JSON only, for example:
{{"adherence": 7, "orchestration": 6, "dynamics": 5, "structure": 6, "overall": 6, "advice": "make the brass louder in the climax"}}"""


def parse_judgement(text: str) -> dict:
    out = {c: math.nan for c in CRITERIA}
    out["advice"] = ""
    m = re.search(r"\{.*\}", text, flags=re.S)
    if m:
        try:
            data = json.loads(m.group(0))
            for c in CRITERIA:
                v = data.get(c)
                if isinstance(v, (int, float)) and 1 <= v <= 10:
                    out[c] = float(v)
            out["advice"] = str(data.get("advice", ""))[:300]
            return out
        except json.JSONDecodeError:
            pass
    for c in CRITERIA:  # tolerant fallback: "adherence: 7"
        mm = re.search(rf"{c}\W+(\d+(?:\.\d+)?)", text, flags=re.I)
        if mm and 1 <= float(mm.group(1)) <= 10:
            out[c] = float(mm.group(1))
    return out


class AudioJudge:
    def __init__(self, model_id: str = "Qwen/Qwen2-Audio-7B-Instruct", max_new_tokens: int = 200):
        import torch
        from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration
        self.torch = torch
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.processor = AutoProcessor.from_pretrained(model_id)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model = Qwen2AudioForConditionalGeneration.from_pretrained(
            model_id, torch_dtype=dtype, device_map="auto").eval()
        self.sr = self.processor.feature_extractor.sampling_rate

    def info(self) -> dict:
        return {"model": self.model_id, "revision": getattr(self.model.config, "_commit_hash", None),
                "decoding": "greedy", "rubric_version": 1}

    def judge(self, audio_path, request: str) -> dict:
        import librosa
        y, _ = librosa.load(str(audio_path), sr=self.sr, mono=True, duration=30.0)
        conversation = [{"role": "user", "content": [
            {"type": "audio", "audio_url": str(audio_path)},
            {"type": "text", "text": RUBRIC.format(request=request)}]}]
        text = self.processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        try:
            inputs = self.processor(text=text, audios=[y], sampling_rate=self.sr, return_tensors="pt", padding=True)
        except TypeError:
            inputs = self.processor(text=text, audio=[y], sampling_rate=self.sr, return_tensors="pt", padding=True)
        inputs = inputs.to(self.model.device)
        with self.torch.no_grad():
            ids = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens, do_sample=False)
        ids = ids[:, inputs["input_ids"].size(1):]
        raw = self.processor.batch_decode(ids, skip_special_tokens=True)[0]
        result = parse_judgement(raw)
        result["raw"] = raw
        return result
