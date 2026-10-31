# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Stage 1: Orchestral Intent Specification.

Turns a free-text request into a structured, deterministic specification. The parser is
rule-based on purpose: every decision is inspectable and identical on every run.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .instruments import (
    ENSEMBLES,
    FAMILIES,
    FAMILY_DEFAULTS,
    FAMILY_WORDS,
    INSTRUMENTS,
    STRING_QUARTET,
)

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    # Raga approximations in 12-tone equal temperament (ornaments are added separately).
    "raga_yaman": [0, 2, 4, 6, 7, 9, 11],
    "raga_bhairav": [0, 1, 4, 5, 7, 8, 11],
    "raga_kafi": [0, 2, 3, 5, 7, 9, 10],
    "raga_bhairavi": [0, 1, 3, 5, 7, 8, 10],
    "raga_desh": [0, 2, 4, 5, 7, 9, 10],
}

# mood -> (scale, tempo BPM, tonic pitch class)
MOODS = {
    "heroic": ("major", 112, 2),
    "triumphant": ("major", 104, 0),
    "majestic": ("major", 92, 3),
    "epic": ("minor", 120, 2),
    "tragic": ("minor", 60, 0),
    "melancholic": ("minor", 70, 9),
    "mysterious": ("dorian", 80, 4),
    "dark": ("phrygian", 84, 4),
    "tense": ("harmonic_minor", 108, 7),
    "joyful": ("major", 132, 7),
    "playful": ("major", 140, 5),
    "serene": ("lydian", 66, 5),
    "romantic": ("major", 80, 8),
    "festive": ("mixolydian", 124, 7),
    "devotional": ("major", 72, 0),
}
MOOD_SYNONYMS = {
    "sad": "melancholic", "melancholy": "melancholic", "mournful": "tragic", "grief": "tragic",
    "calm": "serene", "peaceful": "serene", "gentle": "serene", "tender": "romantic",
    "love": "romantic", "happy": "joyful", "bright": "joyful", "cheerful": "joyful",
    "suspense": "tense", "suspenseful": "tense", "anxious": "tense", "ominous": "dark",
    "sinister": "dark", "eerie": "mysterious", "magical": "mysterious", "grand": "majestic",
    "noble": "majestic", "victorious": "triumphant", "celebration": "festive",
    "celebratory": "festive", "spiritual": "devotional", "prayer": "devotional",
    "cinematic": "epic", "adventurous": "heroic", "brave": "heroic", "whimsical": "playful",
}
DEFAULT_MOOD = "majestic"

FORMS = {
    "overture": [("Introduction", 1), ("Theme A", 2), ("Theme B", 2), ("Development", 2),
                 ("Recapitulation", 2), ("Coda", 1)],
    "sonata": [("Exposition", 3), ("Development", 2), ("Recapitulation", 3), ("Coda", 1)],
    "theme_variations": [("Theme", 2), ("Variation 1", 2), ("Variation 2", 2),
                         ("Variation 3", 2), ("Finale", 2)],
    "rondo": [("A", 2), ("B", 2), ("A", 2), ("C", 2), ("A", 2)],
    "film_cue": [("Atmosphere", 2), ("Build", 3), ("Hit", 2), ("Resolve", 2)],
    "song": [("Intro", 1), ("Verse", 2), ("Chorus", 2), ("Verse", 2), ("Chorus", 2), ("Outro", 1)],
    "march": [("Introduction", 1), ("March", 3), ("Trio", 3), ("March", 3)],
    "chorale": [("Phrase 1", 1), ("Phrase 2", 1), ("Phrase 3", 1), ("Phrase 4", 1)],
    "raga_form": [("Alap", 2), ("Jor", 2), ("Gat", 3), ("Jhala", 2)],
    "through_composed": [("Opening", 2), ("Development", 3), ("Climax", 2), ("Close", 2)],
}
FORM_WORDS = [
    ("theme and variations", "theme_variations"), ("variations", "theme_variations"),
    ("overture", "overture"), ("sonata", "sonata"), ("rondo", "rondo"),
    ("film cue", "film_cue"), ("trailer", "film_cue"), ("soundtrack", "film_cue"),
    ("cue", "film_cue"), ("verse", "song"), ("song", "song"), ("track", "song"), ("march", "march"),
    ("chorale", "chorale"), ("hymn", "chorale"), ("alap", "raga_form"),
]
FORM_DEFAULT_SHAPE = {
    "overture": "arch", "sonata": "arch", "theme_variations": "crescendo", "rondo": "terraced",
    "film_cue": "crescendo", "song": "terraced", "march": "terraced", "chorale": "arch",
    "raga_form": "crescendo", "through_composed": "arch",
}
DYNAMIC_SHAPES = ("crescendo", "decrescendo", "arch", "terraced", "flat")

CRESC_WORDS = ("starts quietly", "start quietly", "builds", "build up", "building", "growing",
               "ending fortissimo", "ends fortissimo", "crescendo", "grows",
               "rises", "swells", "ends with full", "ending with full", "towards a climax")
DECRESC_WORDS = ("fades", "fade out", "dies away", "dying away", "decrescendo", "diminuendo", "ends quietly",
                 "ending quietly", "ends softly", "settles")
TERRACED_WORDS = ("contrast", "loud and soft", "terraced", "alternating", "call and response")
FLAT_WORDS = ("steady", "constant", "even dynamics", "ambient", "throughout")

CULTURE_WORDS = [
    ("raga yaman", "raga_yaman"), ("yaman", "raga_yaman"), ("raga bhairav", "raga_bhairav"),
    ("bhairavi", "raga_bhairavi"), ("bhairav", "raga_bhairav"), ("raga kafi", "raga_kafi"),
    ("kafi", "raga_kafi"), ("raga desh", "raga_desh"), ("garba", "garba"),
    ("gujarati", "garba"), ("bollywood", "bollywood"), ("indian classical", "raga_kafi"),
    ("indian", "indian"), ("raga", "raga_kafi"),
]
CULTURE_SCALE = {"garba": "mixolydian", "bollywood": "harmonic_minor", "indian": "raga_kafi"}
CULTURE_METRE = {"garba": 6}

PITCH_CLASSES = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


@dataclass
class OrchestralSpec:
    request_id: str
    text: str
    ensemble: str
    families: list[str]
    instruments: list[str]
    mood: str
    scale: str
    tonic: int
    tempo: int
    metre: int
    form: str
    dynamics_shape: str
    culture: str | None = None
    lyrics: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _find(words, text):
    """Return the first (position, value) of any phrase found as whole words."""
    best = None
    for phrase, value in words:
        m = re.search(rf"\b{re.escape(phrase)}\b", text)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), value)
    return best


def parse_request(request_id: str, text: str, lyrics: str | None = None) -> OrchestralSpec:
    raw = text.strip()
    t = " " + raw.lower() + " "
    notes: list[str] = []

    # Ensemble (longest phrase first).
    ensemble = None
    for name in sorted(ENSEMBLES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", t):
            ensemble = name
            break

    # Named instruments (longest alias first, consumed so 'bass drum' is not also 'bass').
    work = t
    found: list[tuple[int, str]] = []
    aliases = sorted(((a, k) for k, ins in INSTRUMENTS.items() for a in ins.aliases),
                     key=lambda x: len(x[0]), reverse=True)
    for alias, key in aliases:
        for m in re.finditer(rf"\b{re.escape(alias)}\b", work):
            found.append((m.start(), key))
            work = work[:m.start()] + " " * (m.end() - m.start()) + work[m.end():]
    found.sort()
    instruments: list[str] = []
    for _, key in found:
        if key not in instruments:
            instruments.append(key)

    families: list[str] = []
    if ensemble:
        families.extend(ENSEMBLES[ensemble])
    for key in instruments:
        fam = INSTRUMENTS[key].family
        if fam not in families:
            families.append(fam)
    for fam, words in FAMILY_WORDS.items():
        if fam not in families and any(re.search(rf"\b{re.escape(w)}\b", work) for w in words):
            families.append(fam)

    # Culture.
    culture_hit = _find(CULTURE_WORDS, t)
    culture = culture_hit[1] if culture_hit else None
    if culture and "world" not in families and culture != "bollywood":
        families.append("world")
        notes.append("culture tag implies Indian instruments")
    if culture == "bollywood" and "world" not in families:
        families.append("world")

    if not families:
        families = list(ENSEMBLES["orchestra"])
        ensemble = ensemble or "orchestra"
        notes.append("no ensemble named: default orchestra")
    families = [f for f in FAMILIES if f in families]  # canonical order

    # Fill families that have no explicit instrument with defaults.
    if ensemble == "string quartet" and not any(INSTRUMENTS[k].family == "strings" for k in instruments):
        instruments = list(dict.fromkeys(STRING_QUARTET)) + instruments  # violin, viola, cello
    for fam in families:
        if not any(INSTRUMENTS[k].family == fam for k in instruments):
            instruments.extend(FAMILY_DEFAULTS[fam])
    if lyrics and "voices" in families and "rap_voice" not in instruments and "rap" in t:
        instruments.append("rap_voice")

    # Mood, scale, tempo, metre.
    mood_words = [(m, m) for m in MOODS] + list(MOOD_SYNONYMS.items())
    mood_hit = _find(mood_words, t)
    mood = mood_hit[1] if mood_hit else DEFAULT_MOOD
    scale, tempo, tonic = MOODS[mood]
    if culture:
        scale = culture if culture.startswith("raga_") else CULTURE_SCALE.get(culture, scale)
    key_m = re.search(r"\bin ([a-g])( ?(?:#|sharp|b|flat))? (major|minor)\b", t)
    if key_m:
        tonic = PITCH_CLASSES[key_m.group(1)]
        acc = (key_m.group(2) or "").strip()
        tonic = (tonic + (1 if acc in ("#", "sharp") else -1 if acc in ("b", "flat") else 0)) % 12
        if not culture:
            scale = key_m.group(3)
    bpm_m = re.search(r"\b(\d{2,3}) ?bpm\b", t)
    if bpm_m:
        tempo = int(bpm_m.group(1))
    elif re.search(r"\b(very slow|adagio|largo)\b", t):
        tempo = 56
    elif re.search(r"\bslow\b", t):
        tempo = min(tempo, 72)
    elif re.search(r"\b(fast|allegro|presto|driving)\b", t):
        tempo = max(tempo, 132)
    metre = 4
    if re.search(r"\b(waltz|3/4)\b", t):
        metre = 3
    elif re.search(r"\b(6/8|jig)\b", t):
        metre = 6
    elif culture in CULTURE_METRE:
        metre = CULTURE_METRE[culture]

    # Form and dynamic shape.
    form_hit = _find(FORM_WORDS, t)
    form = form_hit[1] if form_hit else ("raga_form" if culture and culture.startswith("raga_")
                                          else "through_composed")
    if lyrics and form == "through_composed":
        form = "song"
    cresc = any(w in t for w in CRESC_WORDS)
    decresc = any(w in t for w in DECRESC_WORDS)
    if cresc and decresc:
        shape = "arch"
    elif cresc:
        shape = "crescendo"
    elif decresc:
        shape = "decrescendo"
    elif any(w in t for w in TERRACED_WORDS):
        shape = "terraced"
    elif any(w in t for w in FLAT_WORDS):
        shape = "flat"
    else:
        shape = FORM_DEFAULT_SHAPE[form]

    return OrchestralSpec(
        request_id=request_id, text=raw, ensemble=ensemble or "custom ensemble",
        families=families, instruments=instruments, mood=mood, scale=scale, tonic=tonic,
        tempo=int(tempo), metre=metre, form=form, dynamics_shape=shape, culture=culture,
        lyrics=lyrics, notes=notes,
    )


def family_f1(predicted: list[str], target: list[str]) -> float:
    """F1 between parsed and target instrument families (intent-parser accuracy)."""
    p, g = set(predicted), set(target)
    if not p and not g:
        return 1.0
    tp = len(p & g)
    if tp == 0:
        return 0.0
    prec, rec = tp / len(p), tp / len(g)
    return 2 * prec * rec / (prec + rec)
