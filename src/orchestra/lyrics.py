# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Lyrics: read your own lyric files, or write lyrics with a free open language model,
and check how well each line fits the planned tempo and bar structure.

Lyric file format (plain text, UTF-8), one tag per section:

    [verse]
    first line
    second line
    [chorus]
    ...

Allowed tags: [intro] [verse] [pre-chorus] [chorus] [bridge] [rap] [outro].
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TAGS = ("intro", "verse", "pre-chorus", "chorus", "bridge", "rap", "outro")


@dataclass
class LyricSection:
    tag: str
    lines: list[str]


def parse_lyrics(text: str) -> list[LyricSection]:
    sections: list[LyricSection] = []
    current: LyricSection | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.fullmatch(r"\[([a-zA-Z\- ]+?)(?:\s*\d+)?\]", line)
        if m:
            tag = m.group(1).strip().lower()
            if tag not in TAGS:
                raise ValueError(f"unknown lyric tag [{tag}]; use one of {', '.join(TAGS)}")
            current = LyricSection(tag, [])
            sections.append(current)
            continue
        if current is None:
            current = LyricSection("verse", [])
            sections.append(current)
        current.lines.append(line)
    if not any(s.lines for s in sections):
        raise ValueError("the lyric file has no lines")
    return sections


def load_lyrics(path) -> tuple[str, list[LyricSection]]:
    text = Path(path).read_text(encoding="utf-8")
    return text, parse_lyrics(text)


def count_syllables(line: str) -> int:
    """Rough syllable count (vowel groups) that also works for romanised Hindi/Gujarati."""
    words = re.findall(r"[a-zA-Z']+", line.lower())
    total = 0
    for w in words:
        groups = re.findall(r"[aeiouy]+", w)
        n = len(groups)
        if w.endswith("e") and n > 1 and not w.endswith(("le", "ee")):
            n -= 1
        total += max(1, n)
    # Lines in non-Latin scripts: estimate one syllable per character cluster.
    if not words:
        total = len(re.findall(r"\w", line)) // 2
    return total


def target_syllables(tempo: int, metre: int, rap: bool = False, bars_per_line: int = 2) -> tuple[int, int]:
    """Comfortable syllable range for one sung line at this tempo."""
    beats = metre * bars_per_line
    per_beat = 2.0 if tempo < 80 else 1.5 if tempo < 120 else 1.0
    if rap:
        per_beat *= 2
    centre = beats * per_beat
    return max(3, int(centre * 0.6)), int(centre * 1.4) + 1


def lyric_fit(sections: list[LyricSection], tempo: int, metre: int) -> dict:
    lo, hi = target_syllables(tempo, metre, rap=any(s.tag == "rap" for s in sections))
    counts = [count_syllables(l) for s in sections for l in s.lines]
    inside = sum(lo <= c <= hi for c in counts)
    return {"lines": len(counts), "syllable_range": [lo, hi], "lines_in_range": inside,
            "fit": inside / len(counts) if counts else 0.0,
            "too_long": [l for s in sections for l in s.lines if count_syllables(l) > hi]}


def form_tags(form: str) -> list[str]:
    if form == "song":
        return ["intro", "verse", "chorus", "verse", "chorus", "outro"]
    return ["verse", "chorus", "verse", "chorus", "bridge", "chorus"]


class LyricsWriter:
    """Writes lyrics with a free open instruction model (default Qwen2.5-7B-Instruct)."""

    def __init__(self, model_id: str = "Qwen/Qwen2.5-7B-Instruct", temperature: float = 0.8,
                 max_new_tokens: int = 500):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.model_id = model_id
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.tok = AutoTokenizer.from_pretrained(model_id)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype, device_map="auto").eval()

    def info(self) -> dict:
        return {"model": self.model_id, "temperature": self.temperature,
                "revision": getattr(self.model.config, "_commit_hash", None)}

    def write(self, request: str, mood: str, tempo: int, metre: int, form: str, language: str = "English",
              theme: str | None = None, seed: int = 11) -> str:
        tags = form_tags(form)
        lo, hi = target_syllables(tempo, metre, rap="rap" in request.lower())
        layout = "\n".join(f"[{t}]" for t in tags)
        prompt = (f"Write original song lyrics in {language} for this piece: \"{request}\". "
                  f"Mood: {mood}. Tempo {tempo} BPM. {('Theme: ' + theme + '. ') if theme else ''}"
                  f"Use exactly these section tags in this order, each on its own line:\n{layout}\n"
                  f"Write 4 lines per verse and chorus and 2 lines for intro, bridge and outro. Each line must "
                  f"have between {lo} and {hi} syllables so it fits two bars. The chorus must be memorable and "
                  f"repeat its key phrase. Do not copy any existing song. Output only the tagged lyrics.")
        msgs = [{"role": "system", "content": "You are a skilled, original lyricist."},
                {"role": "user", "content": prompt}]
        text = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = self.tok([text], return_tensors="pt").to(self.model.device)
        self.torch.manual_seed(seed)
        with self.torch.no_grad():
            ids = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens, do_sample=True,
                                      temperature=self.temperature, top_p=0.95)
        out = self.tok.decode(ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        parse_lyrics(out)  # raises if the model ignored the format
        return out
