# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Stage 2: Orchestration engine.

Assigns a role (melody, harmony, bass, rhythm, colour) to every requested instrument,
chooses idiomatic registers inside each instrument's range, sets section balance, and
reports problems it found and repaired.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .instruments import INSTRUMENTS
from .intent import OrchestralSpec

MELODY_PRIORITY = ["sitar", "shehnai", "bansuri", "rap_voice", "soprano", "choir", "violin",
                   "flute", "oboe", "clarinet", "trumpet", "horn", "cello", "piano", "synth_pad"]
BASS_PRIORITY = ["double_bass", "tuba", "sub_bass", "contrabassoon", "bass_trombone", "bassoon",
                 "bass_clarinet", "bass_voice", "cello", "trombone", "piano", "harp", "organ"]

# Relative gain per family so that loud families do not cover quiet ones (balance).
FAMILY_BALANCE = {"strings": 1.0, "woodwinds": 1.05, "brass": 0.85, "percussion": 0.9,
                  "keyboards": 0.95, "voices": 1.05, "world": 1.0, "electronic": 0.9}


@dataclass
class Part:
    instrument: str
    family: str
    role: str
    register_low: int
    register_high: int
    balance: float


@dataclass
class OrchestrationPlan:
    parts: list[Part]
    lead: str
    bass: str | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def part(self, key: str) -> Part | None:
        return next((p for p in self.parts if p.instrument == key), None)


def _register(ins, role: str) -> tuple[int, int]:
    """Pick a comfortable band inside the range for the role (avoid extreme edges)."""
    lo, hi = ins.low, ins.high
    span = hi - lo
    if role == "melody":
        return lo + span * 35 // 100, lo + span * 85 // 100
    if role == "bass":
        return lo, lo + span * 50 // 100
    if role == "colour":
        return lo + span * 40 // 100, hi
    return lo + span * 20 // 100, lo + span * 70 // 100  # harmony / rhythm


def orchestrate(spec: OrchestralSpec) -> OrchestrationPlan:
    keys = list(dict.fromkeys(spec.instruments))
    warnings: list[str] = []
    pitched = [k for k in keys if not INSTRUMENTS[k].is_drum]

    lead = next((k for k in MELODY_PRIORITY if k in pitched), pitched[0] if pitched else keys[0])
    bass = next((k for k in BASS_PRIORITY if k in pitched and k != lead), None)
    if bass is None and len(pitched) > 1:
        bass = min((k for k in pitched if k != lead), key=lambda k: INSTRUMENTS[k].low)
        warnings.append(f"no natural bass instrument: {bass} takes the bass line")

    parts: list[Part] = []
    for k in keys:
        ins = INSTRUMENTS[k]
        if ins.is_drum or k == "timpani":
            role = "rhythm"
        elif k == lead:
            role = "melody"
        elif k == bass:
            role = "bass"
        elif ins.role == "colour":
            role = "colour"
        elif ins.role == "melody":
            role = "countermelody"
        else:
            role = "harmony"
        lo, hi = (0, 127) if ins.is_drum else _register(ins, "melody" if role == "countermelody" else role)
        parts.append(Part(k, ins.family, role, lo, hi, FAMILY_BALANCE[ins.family]))

    # Balance checks.
    fam_count = {}
    for p in parts:
        fam_count[p.family] = fam_count.get(p.family, 0) + 1
    if fam_count.get("brass", 0) > fam_count.get("strings", 0) + 1 and "strings" in fam_count:
        warnings.append("brass outnumber strings: brass gain reduced further")
        for p in parts:
            if p.family == "brass":
                p.balance = round(p.balance * 0.85, 3)
    if INSTRUMENTS[lead].family == "woodwinds" and "brass" in fam_count:
        warnings.append("woodwind melody over brass: brass kept to harmony at lower gain")
        for p in parts:
            if p.family == "brass" and p.role != "melody":
                p.balance = round(p.balance * 0.9, 3)
    return OrchestrationPlan(parts=parts, lead=lead, bass=bass, warnings=warnings)
