# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Stage 3: Conductor layer.

Plans the large-scale shape of a piece: section timings, a dynamic marking per section,
which families play, which family leads, articulation and tempo changes. The same
functions also build the *target* plan used for evaluation, from the fixed benchmark
targets, so every condition is scored against an identical reference.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .intent import FORMS, OrchestralSpec

MARKS = ["pp", "p", "mp", "mf", "f", "ff", "fff"]
MARK_DB = {"pp": -30.0, "p": -24.0, "mp": -18.0, "mf": -14.0, "f": -9.0, "ff": -5.0, "fff": -2.0}
MARK_VELOCITY = {"pp": 32, "p": 45, "mp": 58, "mf": 72, "f": 90, "ff": 108, "fff": 122}
RAGA_TEMPO = {"Alap": 0.6, "Jor": 0.9, "Gat": 1.0, "Jhala": 1.35}
LEAD_ORDER = ["world", "voices", "woodwinds", "strings", "keyboards", "brass", "electronic", "percussion"]


@dataclass
class SectionPlan:
    name: str
    start: float
    end: float
    mark: str
    tempo: int
    lead_family: str
    active_families: list[str]
    articulation: str
    accent: bool = False  # set by song-mode refinement: mark the section change clearly

    @property
    def level_db(self) -> float:
        return MARK_DB[self.mark]


def shape_marks(shape: str, n: int) -> list[str]:
    """Dynamic marking per section for a named dynamic shape."""
    if n <= 0:
        return []
    if shape == "crescendo":
        idx = np.linspace(0, 5, n)
    elif shape == "decrescendo":
        idx = np.linspace(5, 0, n)
    elif shape == "arch":
        peak = max(1, round((n - 1) * 0.66))
        idx = np.array([5.5 * i / peak if i <= peak else 5.5 - 4.5 * (i - peak) / max(1, n - 1 - peak)
                        for i in range(n)])
        idx[0] = min(idx[0], 1)
    elif shape == "terraced":
        idx = np.array([4.5 if i % 2 else 1.5 for i in range(n)])
        idx[-1] = 5
    else:  # flat
        idx = np.full(n, 3.0)
    return [MARKS[int(round(min(6, max(0, v))))] for v in idx]


def _articulation(mark: str, family: str) -> str:
    loud = MARKS.index(mark) >= 4
    soft = MARKS.index(mark) <= 1
    table = {
        "strings": "tremolo and sul tasto" if soft else "marcato and spiccato" if loud else "legato",
        "woodwinds": "soft sustained solo lines" if soft else "bright doubled runs" if loud else "lyrical phrases",
        "brass": "muted, distant horns" if soft else "full fanfare chords" if loud else "warm chorale",
        "percussion": "quiet timpani rolls" if soft else "timpani hits and cymbal crashes" if loud else "soft pulse",
        "keyboards": "harp arpeggios" if not loud else "harp glissandi and celesta sparkle",
        "voices": "humming choir" if soft else "full choir fortissimo" if loud else "choir on open vowels",
        "world": "slow alap with meend" if soft else "fast tabla and sitar jhala" if loud else "gat with tabla",
        "electronic": "low synth drone" if soft else "trailer hits and sub bass" if loud else "pulsing synth pad",
    }
    return table.get(family, "legato")


def plan_sections(form: str, shape: str, families: list[str], duration: float, tempo: int,
                  lead_family: str | None = None) -> list[SectionPlan]:
    template = FORMS[form]
    weights = np.array([w for _, w in template], dtype=float)
    bounds = np.concatenate([[0.0], np.cumsum(weights) / weights.sum() * duration])
    marks = shape_marks(shape, len(template))
    fams_by_lead = [f for f in LEAD_ORDER if f in families] or families
    sections: list[SectionPlan] = []
    for i, ((name, _), mark) in enumerate(zip(template, marks)):
        level = MARKS.index(mark)
        if level >= 5:
            lead = "brass" if "brass" in families else (lead_family or fams_by_lead[0])
        elif i == 0:
            lead = lead_family or fams_by_lead[0]
        else:
            lead = fams_by_lead[i % len(fams_by_lead)]
        n_active = max(1, int(np.ceil(len(families) * (level + 1) / 7)))
        active = [lead] + [f for f in fams_by_lead if f != lead][: n_active - 1]
        active = [f for f in families if f in active]  # canonical order
        sec_tempo = int(round(tempo * RAGA_TEMPO.get(name, 1.0)))
        sections.append(SectionPlan(name, round(float(bounds[i]), 3), round(float(bounds[i + 1]), 3),
                                    mark, sec_tempo, lead, active, _articulation(mark, lead)))
    return sections


def conduct(spec: OrchestralSpec, duration: float, lead_family: str | None = None) -> list[SectionPlan]:
    return plan_sections(spec.form, spec.dynamics_shape, spec.families, duration, spec.tempo, lead_family)


def dynamics_curve(sections: list[SectionPlan], duration: float, hop: float = 1.0) -> np.ndarray:
    """Planned loudness (dB) on a regular time grid, interpolated between section centres."""
    t = np.arange(0.0, duration, hop) + hop / 2
    centres = np.array([(s.start + s.end) / 2 for s in sections])
    levels = np.array([s.level_db for s in sections])
    return np.interp(t, centres, levels)


def boundaries(sections: list[SectionPlan]) -> list[float]:
    """Inner section boundaries in seconds (start and end excluded)."""
    return [s.start for s in sections[1:]]


def sections_to_dicts(sections: list[SectionPlan]) -> list[dict]:
    return [asdict(s) for s in sections]
