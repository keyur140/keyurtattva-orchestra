# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Two purposes for every song:

* ``explore`` - try anything, including research-only models. Outputs are marked
  "not cleared for release".
* ``publish`` (Tattva mode) - only routes whose terms let you own and release the result.
  It checks your declarations, refuses anything that is not cleared, and writes a
  release pack: rights checklist, AI disclosure text, credits and a human-contribution log.

This is a safety net, not legal advice. Model terms change: re-check them before release.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

PURPOSES = ("explore", "publish")

POLICY = {
    "midi": {
        "allowed": True,
        "basis": "Your own rule-based composer writes every note. Rendered with the built-in "
                 "synthesiser or a soundfont you may use commercially (FluidR3_GM is MIT-licensed).",
        "declarations": [],
    },
    "suno": {
        "allowed": True,
        "basis": "Suno paid plan: Suno's terms give subscribers ownership of their outputs and allow "
                 "commercial use (check the current terms before each release).",
        "declarations": ["SUNO_PAID_PLAN"],
    },
    "stable_audio": {
        "allowed": True,
        "basis": "Stability AI Community License: commercial use is allowed below its annual revenue "
                 "limit, once you have accepted the licence (check the current limit).",
        "declarations": ["STABLE_AUDIO_LICENCE_ACCEPTED"],
    },
    "musicgen_melody": {
        "allowed": False,
        "reason": "MusicGen-melody weights are licensed for non-commercial use only. To publish a song "
                  "built on your sung tune, use --generator midi (the orchestra plays your tune).",
    },
    "musicgen": {
        "allowed": False,
        "reason": "MusicGen weights are licensed for non-commercial use only. Use --purpose explore, or "
                  "publish with --generator midi, suno or stable_audio.",
    },
}

DECLARATION_TEXT = {
    "SUNO_PAID_PLAN": "I have an active paid Suno plan that gives me ownership and commercial rights.",
    "STABLE_AUDIO_LICENCE_ACCEPTED": "I have accepted the Stability AI Community License and I am "
                                     "below its annual revenue limit.",
}


class PublishBlocked(RuntimeError):
    pass


def check_publish(generator: str) -> dict:
    """Return the clearance record for a generator, or raise PublishBlocked with the reason."""
    rule = POLICY.get(generator)
    if rule is None or not rule["allowed"]:
        raise PublishBlocked(rule["reason"] if rule else f"{generator} is not cleared for publishing")
    missing = [d for d in rule["declarations"] if os.environ.get(d, "").strip().lower() not in ("yes", "true", "1")]
    if missing:
        lines = "\n".join(f"  {d}=yes   # {DECLARATION_TEXT[d]}" for d in missing)
        raise PublishBlocked(f"Publish mode with {generator} needs your declaration in .env:\n{lines}")
    return {"generator": generator, "basis": rule["basis"],
            "declarations": {d: DECLARATION_TEXT[d] for d in rule["declarations"]},
            "declared_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def release_pack(folder: Path, *, rights: dict, clearance: dict, request: str, lyrics_source: str,
                 lyrics_by_ai: bool, best_version: int, model_name: str, quality: dict | None = None) -> None:
    folder = Path(folder)
    artist, credit = rights["artist"], rights["credit_line"]
    lyric_status = ("Written by AI (Qwen2.5). Weak copyright on its own: rewrite it in your own words "
                    "before release." if lyrics_by_ai else
                    "Yours (your own file)." if lyrics_source.startswith("your file") else "None (instrumental).")
    quality = quality or {}
    qlines = "\n".join(f"- {line}" for line in quality.get("notes", [])) or "- No quality warnings."
    checklist = f"""# Release checklist: {artist}

**Song request:** {request}
**Version to release:** v{best_version}.wav (see BEST.txt and song_report.html)
**Made with:** {model_name}
**Why it is cleared:** {clearance['basis']}

## Rights status

| Part | Status |
| --- | --- |
| Music | Cleared under the publish policy above |
| Lyrics | {lyric_status} |
| Arrangement and plan | Yours: your request, and the pipeline's plan written by your own code |
| Credit and notice | Embedded in every WAV and MIDI file; see OUTPUT_LICENSE.md |
| Proof of date and integrity | manifest.json and SHA256SUMS (run `python run_all.py verify <this folder>`) |

## Sound quality check

Best version score: {quality.get('best_score', 'n/a')} (versions: {quality.get('scores', 'n/a')})

{qlines}

## Before you release

- [ ] Listen to the whole track and make sure it does not resemble an existing song or artist.
- [ ] Add your human contribution: edit, re-record, mix or rewrite. Write what you did in HUMAN_CONTRIBUTIONS.md.
- [ ] Re-check the current terms of the tool you used.
- [ ] Release through a distributor as **{artist}** and answer its AI questions honestly (AI_DISCLOSURE.txt).
- [ ] Register the song and lyrics with PRS for Music, and the recording with PPL (UK).
- [ ] Keep this folder unchanged as your record.

This checklist is general information, not legal advice.
"""
    (folder / "RELEASE_CHECKLIST.md").write_text(checklist, encoding="utf-8")
    disclosure = (f"\"{request}\" by {artist} ({rights['owner']}) was created with AI-assisted tools "
                  f"({model_name}), directed by the artist through a structured composition pipeline. "
                  f"Lyrics: {'AI-assisted, edited by the artist' if lyrics_by_ai else lyrics_source}. "
                  f"Credit: {credit}.\n")
    (folder / "AI_DISCLOSURE.txt").write_text(disclosure, encoding="utf-8")
    (folder / "HUMAN_CONTRIBUTIONS.md").write_text(f"""# Human contributions: {artist}

This file is yours to edit (it is excluded from SHA256SUMS on purpose). List everything you did
by hand: it is the strongest part of your copyright claim.

- {datetime.now(timezone.utc).date()}: wrote the request "{request}"
- {datetime.now(timezone.utc).date()}: chose the lyrics ({lyrics_source})
- {datetime.now(timezone.utc).date()}: reviewed the versions and chose v{best_version}
- (add your edits, re-recordings, mixing and rewritten lines here)
""", encoding="utf-8")


def quality_notes(generator: str, gen_info: dict, scores: list, metrics: dict) -> dict:
    """Honest notes on whether the best version is good enough to release as it is."""
    notes = []
    if generator == "midi" and gen_info.get("renderer") != "fluidsynth":
        notes.append("DEMO SOUND: the built-in synthesiser was used. Before release, set SOUNDFONT_PATH to a "
                     "good orchestral soundfont, or import the .mid file into a DAW with professional "
                     "orchestral instruments (the notes and arrangement stay yours).")
    dyn = metrics.get("dynamics_accuracy")
    if dyn is not None and dyn == dyn and dyn < 0.5:
        notes.append(f"Dynamics follow the plan only weakly (rho {dyn:.2f}); consider more versions or a manual mix.")
    clar = metrics.get("section_clarity_raw")
    if clar is not None and clar == clar and clar < 0.5:
        notes.append(f"Some requested instrument families are hard to hear (clarity {clar:.2f}).")
    clean = [round(float(s), 3) for s in scores if s == s]
    if len(clean) > 1 and clean[-1] < max(clean):
        notes.append("The last version is not the best one; BEST.txt points to the best.")
    return {"best_score": max(clean) if clean else None, "scores": clean, "notes": notes}
