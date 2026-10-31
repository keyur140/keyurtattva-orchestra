# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Symbolic route: specification -> MIDI score -> audio.

* ``pipeline`` condition: a score written from the orchestration and conductor plans.
* ``plain`` condition: the applicant's original v1 generator logic (random scale notes,
  every instrument playing all the time, fixed velocity, no range checks). It is the
  naive symbolic baseline.

Audio is rendered with FluidSynth and a General MIDI soundfont when both are available
(set ``SOUNDFONT_PATH``), otherwise with a small built-in additive synthesiser so the
package always runs.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

from ..conductor import MARK_VELOCITY, MARKS, SectionPlan
from ..instruments import INSTRUMENTS
from ..intent import SCALES, OrchestralSpec
from ..orchestrator import OrchestrationPlan

try:
    import pretty_midi
except ImportError:  # pragma: no cover
    pretty_midi = None

PROGRESSIONS = {
    "major": [0, 5, 3, 4], "lydian": [0, 1, 4, 0], "mixolydian": [0, 6, 3, 0],
    "minor": [0, 5, 3, 4], "harmonic_minor": [0, 3, 4, 0], "dorian": [0, 3, 6, 0],
    "phrygian": [0, 1, 6, 0],
}
RHYTHMS = [[1, 1, 1, 1], [1.5, 0.5, 1, 1], [0.5, 0.5, 1, 2], [2, 1, 1], [1, 0.5, 0.5, 2], [3, 1]]


class MidiGenerator:
    name = "midi"
    conditions = ("plain", "pipeline")
    reproducible = True

    def __init__(self, sample_rate: int = 32000, soundfont: str | None = None):
        if pretty_midi is None:
            raise ImportError("pretty_midi is required for the MIDI route: pip install pretty_midi")
        self.sample_rate = sample_rate
        self.soundfont = soundfont or os.environ.get("SOUNDFONT_PATH") or None

    def info(self) -> dict:
        renderer = "fluidsynth" if self._use_fluidsynth() else "builtin-additive-synth"
        return {"generator": self.name, "model": "rule-based symbolic composer", "renderer": renderer,
                "soundfont": self.soundfont if renderer == "fluidsynth" else None}

    def _use_fluidsynth(self) -> bool:
        return bool(self.soundfont and Path(self.soundfont).is_file() and shutil.which("fluidsynth"))

    # ------------------------------------------------------------------ public API
    def generate(self, *, condition: str, prompt: str, seed: int, duration: float, out_wav: Path,
                 spec: OrchestralSpec, plan: OrchestrationPlan, sections: list[SectionPlan],
                 voice=None, **_) -> dict:
        rng = np.random.default_rng(seed)
        if condition == "pipeline":
            pm, stats = compose_pipeline(spec, plan, sections, duration, rng, voice=voice)
        elif condition == "plain":
            pm, stats = compose_naive(spec, duration, rng)
        else:
            raise ValueError(f"MIDI route has no '{condition}' condition")
        out_wav = Path(out_wav)
        mid_path = out_wav.with_suffix(".mid")
        pm.write(str(mid_path))
        if self._use_fluidsynth():
            subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-F", str(out_wav), "-r",
                            str(self.sample_rate), self.soundfont, str(mid_path)],
                           check=True, capture_output=True)
        else:
            audio = synthesize(pm, self.sample_rate, duration)
            import soundfile as sf
            sf.write(str(out_wav), audio, self.sample_rate, subtype="PCM_16")
        stats.update(self.info())
        stats["midi_file"] = mid_path.name
        return stats


# ---------------------------------------------------------------------- composing helpers
def _scale_pitches(spec: OrchestralSpec) -> list[int]:
    pcs = [(spec.tonic + i) % 12 for i in SCALES[spec.scale]]
    return [p for p in range(0, 128) if p % 12 in pcs]


def _triad(spec: OrchestralSpec, degree: int) -> list[int]:
    steps = SCALES[spec.scale]
    return [(spec.tonic + steps[(degree + k) % 7]) % 12 for k in (0, 2, 4)]


def _nearest(pcs: list[int], lo: int, hi: int, target: int) -> int:
    cands = [p for p in range(lo, hi + 1) if p % 12 in pcs]
    if not cands:
        return max(lo, min(hi, target))
    return min(cands, key=lambda p: abs(p - target))


def _velocity(sec: SectionPlan, nxt: SectionPlan | None, t: float, balance: float) -> int:
    v0 = MARK_VELOCITY[sec.mark]
    v1 = MARK_VELOCITY[nxt.mark] if nxt else v0
    frac = (t - sec.start) / max(1e-6, sec.end - sec.start)
    v = v0 + (v1 - v0) * max(0.0, frac - 0.5) * 2 * 0.5  # ramp in the second half towards the next mark
    return int(max(1, min(127, round(v * balance))))


def _new_instrument(key: str):
    ins = INSTRUMENTS[key]
    if ins.is_drum:
        return pretty_midi.Instrument(program=0, is_drum=True, name=ins.name)
    return pretty_midi.Instrument(program=ins.gm_program, name=ins.name)


def _stable(text: str) -> int:
    """A hash that is the same in every run (Python's hash() of a string is not)."""
    import zlib
    return zlib.crc32(text.encode("utf-8"))


def _best_triad(spec, bar_notes, fallback_degree: int) -> list[int]:
    """The diatonic triad that holds most of the sung notes in this bar (harmonising your tune)."""
    if not bar_notes:
        return _triad(spec, fallback_degree)
    weight = np.zeros(12)
    for a, b, p in bar_notes:
        weight[p % 12] += b - a
    best = max(range(7), key=lambda d: (sum(weight[pc] for pc in _triad(spec, d)), d == fallback_degree, -d))
    return _triad(spec, best)


def compose_pipeline(spec, plan, sections, duration, rng, voice=None):
    """Compose from the plans. With ``voice`` (a VoiceMelody), your sung tune is the theme."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=spec.tempo)
    tracks = {p.instrument: _new_instrument(p.instrument) for p in plan.parts}
    scale = _scale_pitches(spec)
    is_raga = spec.scale.startswith("raga_")
    prog = PROGRESSIONS.get(spec.scale, [0, 0, 4, 0] if is_raga else [0, 5, 3, 4])
    motif_rhythm = RHYTHMS[int(rng.integers(len(RHYTHMS)))]
    motif_steps = [int(s) for s in rng.integers(-2, 3, size=len(motif_rhythm))]
    repairs = 0
    n_notes = 0
    voice_notes_used = 0

    def add(key, pitch, start, end, vel):
        nonlocal repairs, n_notes
        ins = INSTRUMENTS[key]
        if not ins.is_drum:
            fixed = ins.fold_into_range(pitch)
            repairs += int(fixed != pitch)
            pitch = fixed
        end = min(end, duration)
        if end - start > 0.02:
            tracks[key].notes.append(pretty_midi.Note(velocity=vel, pitch=int(pitch), start=float(start), end=float(end)))
            n_notes += 1

    for si, sec in enumerate(sections):
        nxt = sections[si + 1] if si + 1 < len(sections) else None
        beat = 60.0 / sec.tempo
        bar = beat * spec.metre
        loud = MARKS.index(sec.mark) >= 4
        active = [p for p in plan.parts if p.family in sec.active_families]
        fam_parts = [p for p in active if p.family == sec.lead_family and not INSTRUMENTS[p.instrument].is_drum]
        melody_part = next((p for p in fam_parts if p.instrument == plan.lead), None) or \
            next((p for p in fam_parts if p.role in ("melody", "countermelody")), None) or \
            (fam_parts[0] if fam_parts else None)
        t = sec.start
        bar_i = 0
        while t < sec.end - 1e-6:
            bar_end = min(t + bar, sec.end)
            sung = voice.notes_between(t, bar_end, duration) if voice is not None else []
            if is_raga:
                chord = [spec.tonic % 12, (spec.tonic + 7) % 12]
            elif voice is not None:
                chord = _best_triad(spec, sung, prog[bar_i % len(prog)])
            else:
                chord = _triad(spec, prog[bar_i % len(prog)])
            if bar_i == 0 and si > 0 and getattr(sec, "accent", False):  # clear section change
                hit = next((p for p in plan.parts if INSTRUMENTS[p.instrument].is_drum), None) or \
                    plan.part("timpani") or (plan.part(plan.bass) if plan.bass else None)
                if hit is not None:
                    ins = INSTRUMENTS[hit.instrument]
                    note = ins.drum_notes[-1] if ins.is_drum else _nearest([chord[0]], hit.register_low, hit.register_high, hit.register_low + 6)
                    add(hit.instrument, note, t, t + beat, min(127, _velocity(sec, nxt, t, 1.0) + 25))
            for p in active:
                ins = INSTRUMENTS[p.instrument]
                vel = _velocity(sec, nxt, t, p.balance)
                if ins.is_drum:
                    notes = ins.drum_notes
                    if p.instrument in ("tabla", "dhol"):
                        for b in range(spec.metre):
                            add(p.instrument, notes[b % len(notes)], t + b * beat, t + b * beat + beat * 0.5,
                                max(1, vel - (0 if b == 0 else 15)))
                    elif loud or bar_i == 0:
                        add(p.instrument, notes[0], t, t + beat, vel)
                    continue
                if p is melody_part:
                    continue
                if p.instrument == "timpani":
                    root = _nearest([chord[0]], p.register_low, p.register_high, (p.register_low + p.register_high) // 2)
                    if nxt and MARKS.index(nxt.mark) > MARKS.index(sec.mark) and bar_end >= sec.end - 1e-6:
                        k = 0
                        while t + k * beat / 4 < bar_end:  # roll into the next, louder section
                            add("timpani", root, t + k * beat / 4, t + (k + 1) * beat / 4, vel)
                            k += 1
                    elif loud:
                        add("timpani", root, t, t + beat, vel)
                    continue
                centre = (p.register_low + p.register_high) // 2
                if p.role == "bass":
                    add(p.instrument, _nearest([chord[0]], p.register_low, p.register_high, centre), t, bar_end, vel)
                elif p.role == "colour":
                    for k, pc in enumerate(chord + [chord[0]]):
                        st = t + k * bar / 4
                        add(p.instrument, _nearest([pc], p.register_low, p.register_high, centre + 4 * k), st, st + bar / 4, vel)
                else:  # harmony and countermelody: chord tone, repeated when loud
                    pc = chord[(_stable(p.instrument) + bar_i) % len(chord)]
                    pitch = _nearest([pc], p.register_low, p.register_high, centre)
                    if loud and p.family == "strings":
                        k = 0
                        while t + k * beat / 2 < bar_end:
                            add(p.instrument, pitch, t + k * beat / 2, t + (k + 1) * beat / 2, vel)
                            k += 1
                    else:
                        add(p.instrument, pitch, t, bar_end, vel)
            if voice is not None:  # YOUR tune is the theme, passed between the lead families
                carrier = melody_part or next((p for p in active if not INSTRUMENTS[p.instrument].is_drum
                                               and p.role in ("melody", "countermelody", "harmony")), None) \
                    or plan.part(plan.lead)
                if carrier is not None:
                    if carrier.instrument not in tracks:
                        tracks[carrier.instrument] = _new_instrument(carrier.instrument)
                    centre = (carrier.register_low + carrier.register_high) // 2
                    shift = 12 * int(round((centre - voice.median_pitch) / 12))
                    vel = min(127, _velocity(sec, nxt, t, carrier.balance) + 10)
                    for a, b, pitch in sung:
                        add(carrier.instrument, pitch + shift, a, b, vel)
                        voice_notes_used += 1
            elif melody_part is not None:  # the theme, carried by the section's lead family
                centre = (melody_part.register_low + melody_part.register_high) // 2
                pitch = _nearest(chord, melody_part.register_low, melody_part.register_high, centre)
                st = t
                vel = min(127, _velocity(sec, nxt, t, melody_part.balance) + 8)
                variation = (si + bar_i) % 3
                for r, step in zip(motif_rhythm, motif_steps):
                    idx = scale.index(pitch) if pitch in scale else 0
                    idx = max(0, min(len(scale) - 1, idx + step + (1 if variation == 2 else 0)))
                    pitch = scale[idx]
                    add(melody_part.instrument, pitch, st, st + r * beat * 0.95, vel)
                    st += r * beat * spec.metre / 4
            t = bar_end
            bar_i += 1

    for tr in tracks.values():
        if tr.notes:
            pm.instruments.append(tr)
    stats = {"notes": n_notes, "range_repairs": repairs, "range_violations": 0}
    if voice is not None:
        stats.update(voice_tune=True, voice_notes_used=voice_notes_used, voice_key=voice.key_name)
    return pm, stats


def compose_naive(spec, duration, rng):
    """Reproduces the v1 logic: random notes of a mood scale around middle C, fixed velocity."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=spec.tempo)
    scale = [60 + i for i in SCALES.get(spec.scale, SCALES["major"])]
    beat = 60.0 / spec.tempo
    violations = 0
    n = 0
    for key in dict.fromkeys(spec.instruments):
        ins = INSTRUMENTS[key]
        tr = _new_instrument(key)
        t = 0.0
        while t < duration:
            length = float(rng.choice([0.25, 0.5, 0.75, 1.0])) * beat
            pitch = int(rng.integers(35, 60)) if ins.is_drum else int(rng.choice(scale))
            if not ins.in_range(pitch):
                violations += 1
            tr.notes.append(pretty_midi.Note(velocity=103, pitch=pitch, start=t, end=min(duration, t + length)))
            n += 1
            t += length
        pm.instruments.append(tr)
    return pm, {"notes": n, "range_repairs": 0, "range_violations": violations}


# ---------------------------------------------------------------------- built-in synthesiser
TIMBRE = {  # family -> (harmonic amplitudes, attack s, release s, decay per s, vibrato)
    "strings": ([1, .5, .33, .25, .2, .16, .12], .08, .12, 0.0, 0.004),
    "woodwinds": ([1, .05, .35, .04, .2, .03, .1], .04, .08, 0.0, 0.003),
    "brass": ([1, .8, .6, .45, .35, .25, .18], .05, .1, 0.0, 0.002),
    "keyboards": ([1, .4, .2, .1, .05], .005, .3, 2.0, 0.0),
    "voices": ([1, .3, .5, .1, .15, .05], .12, .2, 0.0, 0.006),
    "world": ([1, .7, .5, .6, .3, .4, .2], .005, .2, 1.2, 0.002),
    "electronic": ([1, .5, .33, .25, .2, .16, .14, .12], .02, .1, 0.0, 0.0),
    "percussion": ([1, .2, .05], .002, .3, 3.0, 0.0),
}
PAN = {"violin": -0.5, "viola": 0.1, "cello": 0.4, "double_bass": 0.6, "flute": -0.15, "oboe": 0.05,
       "clarinet": -0.1, "bassoon": 0.15, "horn": -0.35, "trumpet": 0.2, "trombone": 0.35, "tuba": 0.45,
       "harp": -0.6, "timpani": 0.0, "choir": 0.0}


def synthesize(pm, sr: int, duration: float) -> np.ndarray:
    n = int(sr * duration) + sr
    out = np.zeros((n, 2), dtype=np.float64)
    key_by_name = {ins.name: k for k, ins in INSTRUMENTS.items()}
    noise_rng = np.random.default_rng(0)
    for tr in pm.instruments:
        key = key_by_name.get(tr.name, "piano")
        ins = INSTRUMENTS[key]
        pan = PAN.get(key, 0.0)
        gl, gr = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        harm, att, rel, decay, vib = TIMBRE.get(ins.family, TIMBRE["keyboards"])
        for note in tr.notes:
            s0 = int(note.start * sr)
            length = int((note.end - note.start + rel) * sr)
            if length <= 0 or s0 >= n:
                continue
            length = min(length, n - s0)
            tt = np.arange(length) / sr
            amp = (note.velocity / 127.0) ** 2 * 0.08
            if tr.is_drum:
                sig = _drum(note.pitch, tt, noise_rng)
            else:
                f0 = 440.0 * 2 ** ((note.pitch - 69) / 12)
                phase = 2 * np.pi * f0 * (tt + vib * np.sin(2 * np.pi * 5.5 * tt) / (2 * np.pi * 5.5))
                sig = sum(a * np.sin((h + 1) * phase) for h, a in enumerate(harm) if (h + 1) * f0 < sr / 2)
            env = np.minimum(1.0, tt / max(att, 1e-4))
            body = note.end - note.start
            env *= np.where(tt > body, np.exp(-(tt - body) / max(rel / 3, 1e-3)), 1.0)
            if decay:
                env *= np.exp(-decay * tt)
            sig = amp * env * sig
            out[s0:s0 + length, 0] += gl * sig
            out[s0:s0 + length, 1] += gr * sig
    out = out[: int(sr * duration)]
    return np.tanh(out * 1.5).astype(np.float32)  # fixed gain + soft clip: dynamics are preserved


def _drum(pitch: int, tt: np.ndarray, rng) -> np.ndarray:
    noise = rng.standard_normal(len(tt))
    if pitch in (35, 36, 41, 64):  # bass drum, dhol: low thump
        return np.sin(2 * np.pi * (55 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 6)
    if pitch in (60, 61, 62):  # tabla-like: pitched decaying tone
        f = {60: 330, 61: 220, 62: 260}[pitch]
        return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 12) + 0.2 * noise * np.exp(-tt * 40)
    if pitch in (49, 52, 57, 51):  # cymbals / tam-tam
        return noise * np.exp(-tt * 2.5) * 0.6
    return noise * np.exp(-tt * 18)  # snare, claps, others
