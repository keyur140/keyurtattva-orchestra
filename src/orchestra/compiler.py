# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Stage 4: Prompt compiler.

Builds the text given to a text-to-audio model under each experimental condition:

* ``plain``    - the user's request, unchanged (baseline).
* ``expert``   - the request plus a fixed list of quality tags that experienced users add.
* ``pipeline`` - the score-structured prompt compiled from the specification, the
                 orchestration plan and the conductor plan, fitted to a word budget.
"""
from __future__ import annotations

from .conductor import SectionPlan
from .instruments import FAMILIES, INSTRUMENTS
from .intent import OrchestralSpec
from .orchestrator import OrchestrationPlan

CONDITIONS = ("plain", "expert", "pipeline")

EXPERT_TAGS = ("high quality orchestral recording, cinematic, rich detailed instrumentation, "
               "concert hall reverb, wide stereo, professionally mixed and mastered")

NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
FORM_NAMES = {
    "overture": "concert overture", "sonata": "sonata-form movement",
    "theme_variations": "theme and variations", "rondo": "rondo", "film_cue": "film score cue",
    "song": "song", "march": "march", "chorale": "chorale", "raga_form": "raga performance",
    "through_composed": "through-composed piece",
}
CULTURE_TEXT = {
    "garba": "Gujarati garba groove with dhol in 6 beats",
    "bollywood": "Bollywood orchestral style with dholak and lush strings",
    "indian": "Indian classical colour with sitar, tabla and bansuri",
}


def plain_prompt(text: str) -> str:
    return text.strip()


def expert_prompt(text: str) -> str:
    return f"{text.strip().rstrip('.')}. {EXPERT_TAGS}."


def _key_text(spec: OrchestralSpec) -> str:
    tonic = NOTE_NAMES[spec.tonic]
    if spec.scale.startswith("raga_"):
        return f"raga {spec.scale[5:].capitalize()} on {tonic}"
    return f"{tonic} {spec.scale.replace('_', ' ')}"


def _instrument_text(spec: OrchestralSpec, compact: bool) -> str:
    groups: dict[str, list[str]] = {}
    for k in dict.fromkeys(spec.instruments):
        ins = INSTRUMENTS[k]
        groups.setdefault(ins.family, []).append(ins.name.lower())
    ordered = [f for f in FAMILIES if f in groups]
    if compact:
        return ", ".join(ordered)
    return "; ".join(f"{fam} ({', '.join(groups[fam])})" for fam in ordered)


def _structure_text(sections: list[SectionPlan], compact: bool) -> str:
    if compact:
        return ", ".join(f"{s.name} {s.mark}" for s in sections)
    parts = []
    for s in sections:
        tutti = "tutti" if len(s.active_families) >= 4 else ", ".join(s.active_families)
        parts.append(f"{s.name} {s.mark}: {s.articulation}, {tutti}")
    return "; ".join(parts)


def pipeline_prompt(spec: OrchestralSpec, plan: OrchestrationPlan, sections: list[SectionPlan],
                    max_words: int = 90) -> str:
    """Compile the score-structured prompt, dropping detail until it fits ``max_words``."""
    lead = INSTRUMENTS[plan.lead].name.lower()
    bass = INSTRUMENTS[plan.bass].name.lower() if plan.bass else None
    metre = f"{spec.metre}/8" if spec.metre == 6 else f"{spec.metre}/4"
    header = (f"{spec.ensemble.capitalize()}, {spec.mood} {FORM_NAMES[spec.form]} in "
              f"{_key_text(spec)}, {spec.tempo} BPM, {metre}.")
    culture = CULTURE_TEXT.get(spec.culture or "", "") if spec.culture and not spec.culture.startswith("raga_") \
        else ("Hindustani raga with meend and gamak ornaments, tabla tala" if spec.culture else "")
    mix = "Concert hall, natural orchestral balance, wide stereo, high quality recording."

    def build(level: int) -> str:
        compact_instr = level >= 3
        compact_struct = level >= 1
        pieces = [header, f"Instruments: {_instrument_text(spec, compact_instr)}."]
        if level < 4:
            roles = f"Melody on {lead}" + (f", bass line on {bass}" if bass else "") + "."
            pieces.append(roles)
        if culture:
            pieces.append(culture.rstrip(".") + ".")
        pieces.append(f"Structure: {_structure_text(sections, compact_struct)}.")
        if level < 2:
            pieces.append(mix)
        return " ".join(pieces)

    for level in range(5):
        text = build(level)
        if len(text.split()) <= max_words:
            return text
    return " ".join(build(4).split()[:max_words])


def compile_prompt(condition: str, spec: OrchestralSpec, plan: OrchestrationPlan,
                   sections: list[SectionPlan], max_words: int = 90) -> str:
    if condition == "plain":
        return plain_prompt(spec.text)
    if condition == "expert":
        return expert_prompt(spec.text)
    if condition == "pipeline":
        return pipeline_prompt(spec, plan, sections, max_words)
    raise ValueError(f"unknown condition: {condition}")
