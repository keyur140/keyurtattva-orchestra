# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Optional Suno adapter (outside the core, reproducible study).

Suno is a closed, paid service. At the time of writing it has no official public API, so
this adapter talks to whatever HTTP endpoint you configure (``SUNO_API_BASE`` and
``SUNO_API_KEY`` in ``.env``). Make sure your use follows Suno's terms of service.

Expected contract (edit ``_submit``/``_poll`` if your endpoint differs):
    POST {SUNO_API_BASE}/generate  JSON {"prompt", "lyrics", "instrumental"} -> {"id"}
    GET  {SUNO_API_BASE}/clips/{id}                                          -> {"status", "audio_url"}
Results from this adapter are reported separately and never enter the confirmatory tests,
because a closed model cannot be re-run exactly.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path


class SunoGenerator:
    name = "suno"
    conditions = ("plain", "expert", "pipeline")
    reproducible = False

    def __init__(self, timeout_s: int = 600, max_prompt_words: int = 120):
        self.base = os.environ.get("SUNO_API_BASE", "").rstrip("/")
        self.key = os.environ.get("SUNO_API_KEY", "")
        if not self.base or not self.key:
            raise RuntimeError("Suno is optional: set SUNO_API_BASE and SUNO_API_KEY in .env to use it")
        self.timeout_s = timeout_s
        self.max_prompt_words = max_prompt_words

    def info(self) -> dict:
        return {"generator": self.name, "model": "suno (closed service)", "endpoint": self.base,
                "reproducible": False}

    def _req(self, method: str, url: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())

    def _submit(self, prompt: str, lyrics: str | None) -> str:
        res = self._req("POST", f"{self.base}/generate",
                        {"prompt": prompt, "lyrics": lyrics or "", "instrumental": not lyrics})
        return str(res["id"])

    def _poll(self, clip_id: str) -> str:
        t0 = time.time()
        while time.time() - t0 < self.timeout_s:
            res = self._req("GET", f"{self.base}/clips/{clip_id}")
            if res.get("status") in ("complete", "succeeded") and res.get("audio_url"):
                return res["audio_url"]
            if res.get("status") in ("error", "failed"):
                raise RuntimeError(f"Suno generation failed: {res}")
            time.sleep(10)
        raise TimeoutError("Suno generation timed out")

    def generate(self, *, condition, prompt, seed, duration, out_wav, lyrics=None, **_) -> dict:
        url = self._poll(self._submit(prompt, lyrics))
        raw = Path(out_wav).with_suffix(".download")
        urllib.request.urlretrieve(url, raw)
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-t", str(duration),
                        str(out_wav)], check=True)
        raw.unlink(missing_ok=True)
        return self.info()
