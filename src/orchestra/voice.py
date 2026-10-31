# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Voice notes: spoken words become lyrics, and a sung or hummed tune becomes the melody.

Everything runs offline on your own computer; no voice note is uploaded anywhere.

* Words: speech recognition with OpenAI Whisper (open weights, MIT licence) through
  Hugging Face transformers. The transcript is split into lyric lines and sections.
* Tune: pitch tracking with pYIN (librosa), cleaned into notes, with the key and tempo
  estimated from the notes. The song then uses YOUR tune as its main theme: on the MIDI route
  the orchestra plays it and harmonises it; with MusicGen-melody the voice note conditions
  the audio model directly (explore mode only, as those weights are non-commercial).
"""
from __future__ import annotations

import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .intent import SCALES
from .provenance import sha256_file

WHISPER_DEFAULT = "openai/whisper-small"
NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
# Krumhansl-Kessler key profiles.
_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


@dataclass
class VoiceMelody:
    notes: list[tuple[float, float, int]]          # (start s, end s, MIDI pitch)
    duration: float                                 # length of the voice note in seconds
    tonic: int                                      # 0 = C ... 11 = B
    scale: str                                      # "major" or "minor"
    tempo: int                                      # beats per minute
    voiced_ratio: float                             # share of the note where a pitch was heard
    source_sha256: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def key_name(self) -> str:
        return f"{NOTE_NAMES[self.tonic]} {self.scale}"

    @property
    def median_pitch(self) -> int:
        return int(np.median([n[2] for n in self.notes])) if self.notes else 60

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(key=self.key_name, n_notes=len(self.notes), median_pitch=self.median_pitch)
        d["notes"] = [[round(a, 3), round(b, 3), int(p)] for a, b, p in self.notes]
        return d

    def notes_between(self, t0: float, t1: float, song_duration: float):
        """Notes that sound in [t0, t1) when the tune is repeated to fill the song."""
        if not self.notes or self.duration <= 0:
            return []
        loop = max(self.duration, self.notes[-1][1])
        out = []
        k0 = int(t0 // loop)
        k1 = int(t1 // loop) + 1
        for k in range(k0, k1 + 1):
            off = k * loop
            for a, b, p in self.notes:
                s, e = a + off, min(b + off, song_duration)
                if t0 <= s < t1 and e > s:
                    out.append((s, e, p))
        return out


# --------------------------------------------------------------------------- the tune
def _load_audio(path: Path, sr: int) -> np.ndarray:
    import librosa
    y, _ = librosa.load(str(path), sr=sr, mono=True)
    if y.size == 0:
        raise ValueError("the voice note is empty")
    peak = float(np.max(np.abs(y)))
    return y / peak if peak > 0 else y


def estimate_key(notes) -> tuple[int, str]:
    hist = np.zeros(12)
    for a, b, p in notes:
        hist[p % 12] += max(0.0, b - a)
    if hist.sum() == 0:
        return 0, "major"
    best = (-2.0, 0, "major")
    for tonic in range(12):
        for name, prof in (("major", _MAJOR), ("minor", _MINOR)):
            r = float(np.corrcoef(hist, np.roll(prof, tonic))[0, 1])
            if r > best[0]:
                best = (r, tonic, name)
    return best[1], best[2]


def estimate_tempo(notes, default: int = 96) -> int:
    onsets = np.array([n[0] for n in notes])
    if onsets.size < 4:
        return default
    ioi = np.diff(onsets)
    ioi = ioi[(ioi > 0.12) & (ioi < 2.0)]
    if ioi.size < 3:
        return default
    beat = float(np.median(ioi))
    bpm = 60.0 / beat
    while bpm < 70:
        bpm *= 2
    while bpm > 140:
        bpm /= 2
    return int(round(bpm))


def extract_melody(path, *, sr: int = 22050, fmin: str = "C2", fmax: str = "C6",
                   min_note_s: float = 0.09) -> VoiceMelody:
    """Turn a sung, hummed or whistled voice note into clean notes, key and tempo."""
    import librosa
    path = Path(path)
    y = _load_audio(path, sr)
    hop = 256
    f0, voiced, _ = librosa.pyin(y, fmin=librosa.note_to_hz(fmin), fmax=librosa.note_to_hz(fmax),
                                 sr=sr, frame_length=2048, hop_length=hop)
    times = librosa.times_like(f0, sr=sr, hop_length=hop)
    midi = np.full(f0.shape, np.nan)
    ok = voiced & np.isfinite(f0)
    midi[ok] = librosa.hz_to_midi(f0[ok])
    # Median-smooth the pitch track to remove vibrato wobble and single-frame jumps.
    sm = midi.copy()
    for i in range(len(midi)):
        w = midi[max(0, i - 3): i + 4]
        w = w[np.isfinite(w)]
        sm[i] = np.median(w) if (w.size and np.isfinite(midi[i])) else np.nan
    rounded = np.where(np.isfinite(sm), np.round(sm), np.nan)

    notes, start, cur = [], None, None
    frame = hop / sr
    for i, p in enumerate(rounded):
        if np.isfinite(p) and p == cur:
            continue
        if cur is not None and start is not None:
            end = times[i]
            if end - start >= min_note_s:
                notes.append([float(start), float(end), int(cur)])
        start, cur = (times[i], p) if np.isfinite(p) else (None, None)
    if cur is not None and start is not None and times[-1] + frame - start >= min_note_s:
        notes.append([float(start), float(times[-1] + frame), int(cur)])
    # Merge repeated pitches split by a tiny gap (a breath or a consonant).
    merged = []
    for n in notes:
        if merged and n[2] == merged[-1][2] and n[0] - merged[-1][1] < 0.06:
            merged[-1][1] = n[1]
        else:
            merged.append(n)
    notes = [(a, b, p) for a, b, p in merged]

    warnings = []
    ratio = float(np.mean(ok)) if ok.size else 0.0
    if not notes:
        raise ValueError("no tune was found in the voice note: sing or hum clearly, close to the microphone")
    if ratio < 0.2:
        warnings.append("only a little of the voice note had a clear pitch; the tune may be incomplete")
    if len(notes) < 4:
        warnings.append("fewer than 4 notes were found; a longer phrase gives a better theme")
    tonic, scale = estimate_key(notes)
    return VoiceMelody(notes=notes, duration=float(len(y) / sr), tonic=tonic, scale=scale,
                       tempo=estimate_tempo(notes), voiced_ratio=round(ratio, 3),
                       source_sha256=sha256_file(path), warnings=warnings)


def melody_to_midi(melody: VoiceMelody, out_path, program: int = 0) -> Path:
    import pretty_midi
    pm = pretty_midi.PrettyMIDI(initial_tempo=melody.tempo)
    ins = pretty_midi.Instrument(program=program, name="Your tune")
    for a, b, p in melody.notes:
        ins.notes.append(pretty_midi.Note(velocity=90, pitch=int(p), start=a, end=b))
    pm.instruments.append(ins)
    out_path = Path(out_path)
    pm.write(str(out_path))
    return out_path


def apply_to_spec(spec, melody: VoiceMelody):
    """Use the key and tempo of the sung tune, so the orchestra fits your voice."""
    spec.tonic = melody.tonic
    spec.scale = melody.scale if melody.scale in SCALES else "major"
    spec.tempo = melody.tempo
    spec.notes = list(spec.notes) + [f"tune from voice note: {melody.key_name}, {melody.tempo} BPM, "
                                     f"{len(melody.notes)} notes"]
    return spec


def tune_similarity(melody: VoiceMelody, wav_path, sr: int = 22050) -> float | None:
    """How much the generated audio follows the sung tune (0-1): mean cosine similarity between
    the tune's pitch-class profile over time and the audio's chroma, after stretching both to the
    same number of steps. A rough, descriptive check, not a confirmatory measure."""
    try:
        import librosa
        y, _ = librosa.load(str(wav_path), sr=sr, mono=True)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)
    except Exception:
        return None
    steps = 48
    loop = max(melody.duration, melody.notes[-1][1]) if melody.notes else 0
    if loop <= 0 or chroma.shape[1] < 4:
        return None
    seg = len(y) / sr / steps
    tune = np.zeros((12, steps))
    for k in range(steps):
        t0 = k * seg
        for a, b, p in melody.notes_between(t0, t0 + seg, len(y) / sr):
            tune[p % 12, k] += 1
    idx = np.linspace(0, chroma.shape[1] - 1, steps).round().astype(int)
    aud = chroma[:, idx]
    sims = []
    for k in range(steps):
        a, b = tune[:, k], aud[:, k]
        if a.sum() > 0 and b.sum() > 0:
            sims.append(float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b))))
    return round(float(np.mean(sims)), 3) if sims else None


# --------------------------------------------------------------------------- the words
def transcribe(path, model_id: str = WHISPER_DEFAULT, language: str | None = None) -> dict:
    """Speech to text with Whisper, offline after the first model download."""
    try:
        from transformers import pipeline
    except ImportError as e:  # pragma: no cover - depends on the optional model stack
        raise ImportError("speech-to-lyrics needs torch + transformers: "
                          "pip install -r requirements-models.txt") from e
    asr = pipeline("automatic-speech-recognition", model=model_id, chunk_length_s=30)
    kwargs = {"generate_kwargs": {"language": language, "task": "transcribe"}} if language else {}
    out = asr(str(path), **kwargs)
    text = (out.get("text") if isinstance(out, dict) else str(out)).strip()
    return {"text": text, "model": model_id, "language": language or "auto",
            "source_sha256": sha256_file(path)}


def transcript_to_lyrics(text: str, words_per_line: int = 8, lines_per_section: int = 4) -> str:
    """Split a transcript into lyric lines and [Verse]/[Chorus] sections the song mode can read."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        raise ValueError("the voice note has no words that could be recognised")
    lines = []
    for sent in re.split(r"(?<=[.!?।])\s+|,\s+(?=\w)", text):
        words = sent.strip().split()
        while words:
            take = words[:words_per_line]
            if len(words) - words_per_line in (1, 2):  # avoid a tiny last line
                take = words
            lines.append(" ".join(take).rstrip(",;"))
            words = words[len(take):]
    blocks = [lines[i:i + lines_per_section] for i in range(0, len(lines), lines_per_section)]
    out = []
    for i, block in enumerate(blocks):
        tag = "Chorus" if (i % 2 == 1) else f"Verse {i // 2 + 1}"
        out.append(f"[{tag}]")
        out.extend(block)
        out.append("")
    return "\n".join(out).strip() + "\n"


def keep_voice_note(src, folder: Path, name: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    dst = folder / f"{name}{Path(src).suffix.lower() or '.wav'}"
    shutil.copy(src, dst)
    return dst
