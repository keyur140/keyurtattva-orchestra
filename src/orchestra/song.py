# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Song mode: several refined versions of the same song (Stage 5, the feedback loop).

Version 1 uses the pipeline prompt. After each version the piece is measured; the
weakest areas (missing instrument families, flat dynamics, unclear sections, the AI
judge's advice) are turned into an improved prompt or score for the next version. The
same seed is kept for every version, so differences come from the refinement itself.
Later versions are not guaranteed to be better: every version is kept and scored, and
the best one is marked.
"""
from __future__ import annotations

import copy
import math
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from . import AUTHOR
from .compiler import pipeline_prompt
from .conductor import MARKS, conduct, sections_to_dicts
from .evaluate import Evaluator, composite
from .generators import make_generator
from .instruments import FAMILIES, FAMILY_LABELS
from .intent import parse_request
from .lyrics import LyricsWriter, load_lyrics, lyric_fit, parse_lyrics
from .orchestrator import orchestrate
from .provenance import base_manifest, now_iso, sha256_file, sha256_text, write_json, write_sums
from .report import _md_to_html, _pdf
from .publish import PURPOSES, check_publish, quality_notes, release_pack
from .rights import rights_from_config, stamp, write_output_licence


@dataclass
class Refinement:
    weak_families: list[str] = field(default_factory=list)
    dynamics: bool = False
    structure: bool = False
    adherence: bool = False
    advice: str = ""

    def empty(self) -> bool:
        return not (self.weak_families or self.dynamics or self.structure or self.adherence or self.advice)

    def describe(self) -> str:
        bits = []
        if self.weak_families:
            bits.append("make " + " and ".join(self.weak_families) + " more audible")
        if self.dynamics:
            bits.append("stronger dynamic contrast")
        if self.structure:
            bits.append("clearer section changes")
        if self.adherence:
            bits.append("follow the original request more closely")
        if self.advice:
            bits.append(f"AI judge advice: {self.advice}")
        return "; ".join(bits) or "no weakness found: same plan, kept for comparison"


def fix_keys(r: Refinement) -> set[str]:
    keys = {f"family:{f}" for f in r.weak_families}
    keys |= {k for k in ("dynamics", "structure", "adherence") if getattr(r, k)}
    return keys


def diagnose(m: dict, families: list[str], exclude: set[str] | None = None) -> Refinement:
    """Find what is weak. ``exclude`` holds fixes that already made a version worse."""
    exclude = exclude or set()
    r = Refinement()
    fam = {f: m.get(f"fam_{f}") for f in FAMILIES if m.get(f"fam_{f}") is not None}
    if fam:
        others = [v for f, v in fam.items() if f not in families]
        bar = max(others) if others else min(fam.values())
        r.weak_families = [f for f in families if fam.get(f, 0) <= bar and f"family:{f}" not in exclude][:2]
    da = m.get("dynamics_accuracy")
    r.dynamics = da is None or not math.isfinite(da) or da < 0.5
    sf = m.get("structure_f")
    r.structure = sf is not None and math.isfinite(sf) and sf < 0.5
    pa = m.get("prompt_adherence")
    r.adherence = pa is not None and math.isfinite(pa) and pa < 0.25
    r.dynamics = r.dynamics and "dynamics" not in exclude
    r.structure = r.structure and "structure" not in exclude
    r.adherence = r.adherence and "adherence" not in exclude
    r.advice = (m.get("judge_advice") or "").strip()[:160]
    if not (r.weak_families or r.dynamics or r.structure or r.adherence):
        # Nothing below threshold: polish the weakest measured area so the next version still improves.
        parts = {"dynamics": (da + 1) / 2 if da is not None and math.isfinite(da) else None,
                 "structure": sf if sf is not None and math.isfinite(sf) else None,
                 "adherence": min(1.0, pa / 0.6) if pa is not None and math.isfinite(pa) else None}
        parts = {k: v for k, v in parts.items() if v is not None and v < 0.98 and k not in exclude}
        if parts:
            setattr(r, min(parts, key=parts.get), True)
    return r


def accumulate(prev: Refinement, new: Refinement) -> Refinement:
    """Keep earlier fixes and add new ones, so each version builds on the last."""
    return Refinement(weak_families=list(dict.fromkeys(prev.weak_families + new.weak_families))[:3],
                      dynamics=prev.dynamics or new.dynamics, structure=prev.structure or new.structure,
                      adherence=prev.adherence or new.adherence, advice=new.advice or prev.advice)


def refine_text(spec, orch, sections, ref: Refinement, max_words: int) -> str:
    extra = []
    if ref.adherence:
        extra.append(f"Request: {spec.text.rstrip('.')}.")
    if ref.weak_families:
        extra.append("Make the " + ", ".join(ref.weak_families) + " clearly audible and prominent.")
    if ref.dynamics:
        extra.append("Very strong dynamic contrast: soft passages very quiet, climax very loud.")
    if ref.structure:
        extra.append("Distinct sections with clear changes: " + ", ".join(s.name for s in sections) + ".")
    if ref.advice:
        extra.append(ref.advice.rstrip(".") + ".")
    budget = max(30, max_words - sum(len(e.split()) for e in extra))
    base = pipeline_prompt(spec, orch, sections, budget)
    return " ".join(([extra[0]] if ref.adherence else []) + [base] + extra[(1 if ref.adherence else 0):])


def refine_score(orch, sections, ref: Refinement):
    """Symbolic refinement: louder weak families, wider dynamic contrast."""
    orch = copy.deepcopy(orch)
    sections = copy.deepcopy(sections)
    for p in orch.parts:
        if p.family in ref.weak_families:
            p.balance = round(min(1.6, p.balance * 1.35), 3)
    if ref.structure:
        for s in sections:
            s.accent = True
    if ref.dynamics:
        for s in sections:
            i = MARKS.index(s.mark)
            s.mark = MARKS[max(0, i - 1)] if i <= 2 else MARKS[min(6, i + 1)] if i >= 4 else s.mark
    return orch, sections


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "song"


def run_song(root: Path, config_path: Path, request: str, lyrics_path: str | None = None,
             write_lyrics: bool = False, language: str = "English", theme: str | None = None,
             versions: int | None = None, generator: str | None = None, seed: int | None = None,
             duration: float | None = None, judge: bool | None = None, out_dir: Path | None = None,
             log=print, purpose: str = "explore", voice_tune: str | None = None,
             voice_lyrics: str | None = None, voice_language: str | None = None) -> Path:
    root = Path(root)
    cfg_text = Path(config_path).read_text(encoding="utf-8")
    cfg = yaml.safe_load(cfg_text)
    sc = cfg["song"]
    versions = int(versions or sc["versions"])
    gname = generator or sc["generator"]
    seed = int(seed if seed is not None else sc["seed"])
    duration = float(duration or sc["duration_s"])
    gcfg = cfg["study"]["generators"].get(gname, {})
    max_words = gcfg.get("max_prompt_words", 90)
    rights = rights_from_config(cfg)
    if purpose not in PURPOSES:
        raise ValueError(f"purpose must be one of {PURPOSES}")
    clearance = None
    if purpose == "publish":
        clearance = check_publish(gname)  # raises PublishBlocked before anything is generated
        rights.update(purpose="publish", cleared_via=f"{gname}: {clearance['basis']}"[:200])
        if write_lyrics:
            log("[publish] AI-written lyrics have weak copyright on their own. Rewrite them in your own words "
                "before release (the release checklist reminds you).")
    else:
        rights["purpose"] = "explore"

    when = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    song_dir = Path(out_dir or root / "songs") / f"{when}_{_slug(request)}"
    song_dir.mkdir(parents=True, exist_ok=True)

    lyrics_text, lyric_sections, lyrics_source, writer_info = None, None, "none", None
    spec = parse_request("song", request)
    melody, tune_copy, voice_info = None, None, {}
    if voice_tune:  # your sung or hummed tune becomes the theme
        from .voice import extract_melody, keep_voice_note, melody_to_midi
        tune_copy = keep_voice_note(voice_tune, song_dir, "voice_tune")
        melody = extract_melody(tune_copy)
        melody_to_midi(melody, song_dir / "your_tune.mid")
        voice_info["tune"] = {k: v for k, v in melody.to_dict().items() if k != "notes"}
        voice_info["tune"]["file"] = tune_copy.name
        log(f"[voice] your tune: {len(melody.notes)} notes, key {melody.key_name}, {melody.tempo} BPM")
        for w in melody.warnings:
            log(f"[voice] {w}")
        if gname not in ("midi", "musicgen_melody"):
            log(f"[voice] {gname} cannot follow a sung tune, so your tune sets the key and tempo only. "
                "Use --generator midi (the orchestra plays your tune) or musicgen_melody (explore mode).")
    if voice_lyrics and not lyrics_path:  # your spoken words become the lyrics
        from .voice import keep_voice_note, transcribe, transcript_to_lyrics
        words_copy = keep_voice_note(voice_lyrics, song_dir, "voice_words")
        tr = transcribe(words_copy, sc.get("speech_model", "openai/whisper-small"), voice_language)
        (song_dir / "transcript.txt").write_text(tr["text"] + "\n", encoding="utf-8")
        lyrics_text = transcript_to_lyrics(tr["text"])
        lyric_sections = parse_lyrics(lyrics_text)
        (song_dir / "lyrics.txt").write_text(lyrics_text, encoding="utf-8")
        lyrics_source = f"your voice note, transcribed by {tr['model']}"
        voice_info["words"] = {**tr, "file": words_copy.name}
        log(f"[voice] your words: {len(tr['text'].split())} words transcribed into {len(lyric_sections)} sections")
    if lyrics_path:
        lyrics_text, lyric_sections = load_lyrics(lyrics_path)
        lyrics_source = f"your file: {Path(lyrics_path).name}"
        shutil.copy(lyrics_path, song_dir / "lyrics.txt")
    elif write_lyrics and not voice_info.get("words"):
        lw = sc["lyrics_writer"]
        writer = LyricsWriter(lw["model_id"], lw.get("temperature", 0.8), lw.get("max_new_tokens", 500))
        lyrics_text = writer.write(request, spec.mood, spec.tempo, spec.metre, "song", language, theme, seed)
        lyric_sections = parse_lyrics(lyrics_text)
        writer_info = writer.info()
        lyrics_source = f"written by {lw['model_id']} (seed {seed})"
        (song_dir / "lyrics.txt").write_text(lyrics_text + "\n", encoding="utf-8")
        gen_dir = root / "lyrics" / "generated"
        gen_dir.mkdir(parents=True, exist_ok=True)
        (gen_dir / f"{song_dir.name}.txt").write_text(lyrics_text + "\n", encoding="utf-8")
        del writer
    if lyrics_text:
        spec = parse_request("song", request, lyrics=lyrics_text)
    if melody is not None:
        from .voice import apply_to_spec
        spec = apply_to_spec(spec, melody)
    orch = orchestrate(spec)
    sections = conduct(spec, duration)
    fit = lyric_fit(lyric_sections, spec.tempo, spec.metre) if lyric_sections else None
    sings = gname == "suno"
    if lyrics_text and not sings:
        log("[note] open models cannot sing words: the lyrics are saved with the song, and voices sing "
            "wordless lines. Use --generator suno for sung lyrics.")

    metrics_cfg = dict(cfg["study"]["metrics"])
    if judge is not None:
        metrics_cfg["judge"] = {**(metrics_cfg.get("judge") or {}), "enabled": judge}
    gen = make_generator(gname, gcfg.get("options", {}))
    evaluator = Evaluator(metrics_cfg, strict=False, log=log)
    manifest = base_manifest("song", cfg, sha256_text(cfg_text), {
        "request": request, "generator": gen.info(), "evaluator": evaluator.info(), "seed": seed,
        "versions": versions, "duration_s": duration, "lyrics_source": lyrics_source,
        "lyrics_sha256": sha256_text(lyrics_text) if lyrics_text else None, "lyrics_writer": writer_info,
        "lyric_fit": fit, "spec": spec.to_dict(), "orchestration": orch.to_dict(),
        "conductor_plan": sections_to_dicts(sections), "human_participants": False, "output_rights": rights,
        "purpose": purpose, "publish_clearance": clearance, "voice_note": voice_info or None})

    rows = []
    ref = Refinement()
    # Keep-the-best loop: each version starts from the best version so far. A fix that made a
    # version worse is undone and not tried again, so the best score can only stay or rise.
    best_score, best_ref, best_m, rejected = float("-inf"), Refinement(), None, set()
    take_seed, best_seed, new_take = seed, seed, False
    for v in range(1, versions + 1):
        cur_orch, cur_sections = (orch, sections) if v == 1 else refine_score(orch, sections, ref)
        prompt = pipeline_prompt(spec, orch, sections, max_words) if v == 1 else \
            refine_text(spec, orch, sections, ref, max_words)
        wav = song_dir / f"v{v}.wav"
        (song_dir / f"v{v}_prompt.txt").write_text(prompt, encoding="utf-8")
        info = gen.generate(condition="pipeline", prompt=prompt, seed=take_seed, duration=duration, out_wav=wav,
                            spec=spec, plan=cur_orch, sections=cur_sections,
                            lyrics=lyrics_text if sings else None, voice=melody,
                            voice_path=str(tune_copy) if tune_copy else None)
        stamp(wav, rights, title=f"{request[:60]} (v{v})")
        m, _ = evaluator.evaluate(wav, request, sections, spec.families, duration)
        m["score"] = composite(m)
        if melody is not None:  # reported only; never part of the combined score
            from .voice import tune_similarity
            m["tune_similarity"] = tune_similarity(melody, wav)
        score = m["score"] if m["score"] is not None and math.isfinite(m["score"]) else float("-inf")
        if v == 1 or score > best_score + 1e-9:
            outcome = "first version" if v == 1 else "new best: kept"
            best_score, best_ref, best_m, best_seed = score, ref, m, take_seed
        else:
            new = fix_keys(ref) - fix_keys(best_ref)
            rejected |= new
            outcome = "not better: change undone" + (f" ({', '.join(sorted(new))})" if new else "")
        row = {"version": v, "file": wav.name, "audio_sha256": sha256_file(wav), "prompt_sha256": sha256_text(prompt),
               "changes": "first version from the pipeline plan" if v == 1 else
               (f"new take of the best plan (seed {take_seed})" if new_take else ref.describe()),
               "outcome": outcome, "seed": take_seed, **m}
        rows.append(row)
        log(f"version {v}: score {m['score']:.3f} ({row['changes']}) -> {outcome}")
        ref = accumulate(best_ref, diagnose(best_m, spec.families, rejected))
        # Nothing new left to fix: try a fresh take of the best plan with another seed instead of
        # repeating an identical version. Every seed is recorded, so it stays reproducible.
        new_take = fix_keys(ref) == fix_keys(best_ref) and ref.advice == best_ref.advice
        take_seed = seed + 101 * v if new_take else best_seed

    df = pd.DataFrame(rows)
    df.to_csv(song_dir / "versions.csv", index=False)
    best = int(df.loc[df["score"].idxmax(), "version"]) if df["score"].notna().any() else versions
    (song_dir / "BEST.txt").write_text(f"v{best}.wav\n", encoding="utf-8")
    manifest.update({"finished_utc": now_iso(), "best_version": best})
    write_json(song_dir / "manifest.json", manifest)
    model_name = manifest["generator"].get("model", gname)
    write_output_licence(song_dir, rights, [model_name])
    if purpose == "publish":
        best_row = df.loc[df["version"] == best].iloc[0].to_dict()
        quality = quality_notes(gname, manifest["generator"], df["score"].tolist(), best_row)
        release_pack(song_dir, rights=rights, clearance=clearance, request=request, lyrics_source=lyrics_source,
                     lyrics_by_ai=bool(write_lyrics), best_version=best, model_name=model_name, quality=quality)
        for note in quality["notes"]:
            log(f"[quality] {note}")
        if voice_info:
            hc = song_dir / "HUMAN_CONTRIBUTIONS.md"
            today = datetime.now(timezone.utc).date()
            extra = []
            if "tune" in voice_info:
                extra.append(f"- {today}: sang the main tune myself (voice note {voice_info['tune']['file']}, "
                             f"SHA-256 {voice_info['tune']['source_sha256']})")
            if "words" in voice_info:
                extra.append(f"- {today}: spoke the lyrics myself (voice note {voice_info['words']['file']}, "
                             f"SHA-256 {voice_info['words']['source_sha256']})")
            hc.write_text(hc.read_text(encoding="utf-8") + "\n".join(extra) + "\n", encoding="utf-8")
    md = song_report(manifest, df, best, lyrics_source, fit, sings)
    if voice_info:
        vlines = ["## Your voice note", ""]
        if "tune" in voice_info:
            t = voice_info["tune"]
            vlines.append(f"- Tune: {t['n_notes']} notes, key {t['key']}, {t['tempo']} BPM, saved as `your_tune.mid`. "
                          + ("The orchestra plays your tune as the theme and harmonises it."
                             if gname == "midi" else "The audio model was conditioned on your voice note."
                             if gname == "musicgen_melody" else "Your tune set the key and tempo."))
            if "tune_similarity" in df:
                vlines.append(f"- Tune similarity of the best version (0-1, rough): {df.loc[df['version'] == best, 'tune_similarity'].iloc[0]}")
        if "words" in voice_info:
            vlines.append(f"- Words: transcribed by {voice_info['words']['model']} into `lyrics.txt` "
                          "(the raw text is in `transcript.txt`). Edit the lyrics and run again if a word is wrong.")
        md = md.replace("Every file in this folder", "\n".join(vlines) + "\n\nEvery file in this folder")
    (song_dir / "song_report.md").write_text(md, encoding="utf-8")
    (song_dir / "song_report.html").write_text(_md_to_html(md, "Song report"), encoding="utf-8")
    _pdf(md, song_dir / "song_report.pdf")
    write_sums(song_dir)
    log(f"done: {song_dir} (best: v{best})")
    return song_dir


def song_report(manifest, df, best, lyrics_source, fit, sings) -> str:
    cols = [c for c in ["version", "score", "prompt_adherence", "section_clarity_raw", "dynamics_accuracy",
                        "structure_f", "judge_overall", "changes", "outcome", "seed"] if c in df]
    lines = ["# Song report", "",
             f"**Author:** {AUTHOR['name']} (ORCID {AUTHOR['orcid']})  ", f"*{AUTHOR['note']}*", "",
             f"- Request: {manifest['request']}",
             f"- Generator: {manifest['generator'].get('model')}",
             f"- Seed: {manifest['seed']} (starting seed; a \"new take\" version uses the seed shown in its row)",
             f"- Lyrics: {lyrics_source}" + ("" if sings or lyrics_source == "none" else
                                             " (saved with the song; open models cannot sing words)"),
             f"- Best version: **v{best}** (highest combined score)",
             f"- Purpose: " + ("**Tattva publish** (rights-safe route; see RELEASE_CHECKLIST.md)"
                               if manifest.get("purpose") == "publish" else
                               "explore (not cleared for release)"), "",
             "## Versions", "",
             "| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")
    lines += ["", "The combined score is the mean of the available measures, each scaled to 0-1. It is used only "
              "to pick the best version; it is not a validated quality measure.", ""]
    if fit:
        lines += ["## Lyric fit", "",
                  f"{fit['lines_in_range']} of {fit['lines']} lines fit the target of "
                  f"{fit['syllable_range'][0]}-{fit['syllable_range'][1]} syllables per two bars.", ""]
        if fit["too_long"]:
            lines += ["Lines that may be too long to sing comfortably:", ""] + [f"- {l}" for l in fit["too_long"]] + [""]
    lines += ["Every file in this folder is listed with its SHA-256 hash in `SHA256SUMS`.", ""]
    return "\n".join(lines)
