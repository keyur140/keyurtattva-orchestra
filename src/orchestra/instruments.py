# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Orchestration knowledge base: instrument families, sounding ranges and General MIDI mapping.

Ranges are practical sounding ranges as MIDI note numbers (middle C = 60), taken from
standard orchestration references (e.g. Adler, *The Study of Orchestration*). They are
deliberately conservative so that generated parts stay idiomatic.
"""
from __future__ import annotations

from dataclasses import dataclass, field

FAMILIES = [
    "strings",
    "woodwinds",
    "brass",
    "percussion",
    "keyboards",
    "voices",
    "world",
    "electronic",
]

# Text descriptions used for CLAP zero-shot family detection (fixed before data collection).
FAMILY_LABELS = {
    "strings": "an orchestral string section with violins, violas, cellos and double basses",
    "woodwinds": "orchestral woodwinds playing: flute, oboe, clarinet and bassoon",
    "brass": "an orchestral brass section with french horns, trumpets, trombones and tuba",
    "percussion": "orchestral percussion: timpani, bass drum, cymbals and snare drum",
    "keyboards": "harp, piano and celesta",
    "voices": "a choir and singing voices",
    "world": "Indian classical instruments: sitar, tabla, bansuri flute and shehnai",
    "electronic": "electronic synthesizers, synth pads and sub bass",
}


@dataclass(frozen=True)
class Instrument:
    key: str
    name: str
    family: str
    low: int = 0
    high: int = 127
    gm_program: int | None = None  # 0-based General MIDI program; None for drum-kit parts
    drum_notes: tuple[int, ...] = ()  # GM percussion keys when the part is unpitched
    role: str = "harmony"  # melody | harmony | bass | rhythm | colour
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_drum(self) -> bool:
        return self.gm_program is None

    def in_range(self, pitch: int) -> bool:
        return self.is_drum or self.low <= pitch <= self.high

    def fold_into_range(self, pitch: int) -> int:
        """Move a pitch by octaves until it fits the instrument (the orchestrator's repair)."""
        if self.is_drum:
            return pitch
        while pitch < self.low:
            pitch += 12
        while pitch > self.high:
            pitch -= 12
        if pitch < self.low:  # range narrower than an octave: clamp
            pitch = self.low
        return pitch


_I = Instrument
INSTRUMENTS: dict[str, Instrument] = {i.key: i for i in [
    # Strings
    _I("violin", "Violin", "strings", 55, 100, 40, role="melody", aliases=("violin", "violins")),
    _I("viola", "Viola", "strings", 48, 88, 41, role="harmony", aliases=("viola", "violas")),
    _I("cello", "Cello", "strings", 36, 81, 42, role="harmony", aliases=("cello", "cellos", "violoncello")),
    _I("double_bass", "Double bass", "strings", 28, 60, 43, role="bass",
       aliases=("double bass", "contrabass", "basses")),
    # Woodwinds
    _I("piccolo", "Piccolo", "woodwinds", 74, 108, 72, role="colour", aliases=("piccolo",)),
    _I("flute", "Flute", "woodwinds", 60, 96, 73, role="melody", aliases=("flute", "flutes")),
    _I("alto_flute", "Alto flute", "woodwinds", 55, 84, 73, role="colour", aliases=("alto flute",)),
    _I("oboe", "Oboe", "woodwinds", 58, 91, 68, role="melody", aliases=("oboe", "oboes")),
    _I("cor_anglais", "Cor anglais", "woodwinds", 52, 81, 69, role="melody",
       aliases=("cor anglais", "english horn")),
    _I("clarinet", "Clarinet", "woodwinds", 50, 94, 71, role="melody", aliases=("clarinet", "clarinets")),
    _I("bass_clarinet", "Bass clarinet", "woodwinds", 34, 74, 71, role="bass", aliases=("bass clarinet",)),
    _I("bassoon", "Bassoon", "woodwinds", 34, 75, 70, role="bass", aliases=("bassoon", "bassoons")),
    _I("contrabassoon", "Contrabassoon", "woodwinds", 22, 53, 70, role="bass", aliases=("contrabassoon",)),
    _I("saxophone", "Saxophone", "woodwinds", 44, 80, 65, role="melody", aliases=("saxophone", "sax")),
    # Brass
    _I("horn", "French horn", "brass", 35, 77, 60, role="harmony", aliases=("horn", "horns", "french horn")),
    _I("trumpet", "Trumpet", "brass", 54, 84, 56, role="melody", aliases=("trumpet", "trumpets", "fanfare")),
    _I("trombone", "Trombone", "brass", 40, 72, 57, role="harmony", aliases=("trombone", "trombones")),
    _I("bass_trombone", "Bass trombone", "brass", 34, 67, 57, role="bass", aliases=("bass trombone",)),
    _I("tuba", "Tuba", "brass", 28, 60, 58, role="bass", aliases=("tuba",)),
    _I("euphonium", "Euphonium", "brass", 34, 70, 58, role="harmony", aliases=("euphonium",)),
    # Percussion
    _I("timpani", "Timpani", "percussion", 38, 57, 47, role="rhythm", aliases=("timpani", "kettle drum")),
    _I("snare", "Snare drum", "percussion", drum_notes=(38,), role="rhythm", aliases=("snare",)),
    _I("bass_drum", "Bass drum", "percussion", drum_notes=(36,), role="rhythm", aliases=("bass drum",)),
    _I("cymbals", "Cymbals", "percussion", drum_notes=(49, 57), role="colour", aliases=("cymbal", "cymbals")),
    _I("tam_tam", "Tam-tam", "percussion", drum_notes=(52,), role="colour", aliases=("tam-tam", "gong")),
    _I("triangle", "Triangle", "percussion", drum_notes=(81,), role="colour", aliases=("triangle",)),
    _I("glockenspiel", "Glockenspiel", "percussion", 79, 108, 9, role="colour", aliases=("glockenspiel",)),
    _I("xylophone", "Xylophone", "percussion", 65, 108, 13, role="colour", aliases=("xylophone",)),
    _I("marimba", "Marimba", "percussion", 45, 96, 12, role="colour", aliases=("marimba",)),
    _I("vibraphone", "Vibraphone", "percussion", 53, 89, 11, role="colour", aliases=("vibraphone",)),
    _I("tubular_bells", "Tubular bells", "percussion", 60, 77, 14, role="colour",
       aliases=("tubular bells", "chimes", "bells")),
    # Keyboards and plucked
    _I("harp", "Harp", "keyboards", 24, 103, 46, role="harmony", aliases=("harp",)),
    _I("piano", "Piano", "keyboards", 21, 108, 0, role="harmony", aliases=("piano",)),
    _I("celesta", "Celesta", "keyboards", 60, 108, 8, role="colour", aliases=("celesta",)),
    _I("harpsichord", "Harpsichord", "keyboards", 29, 89, 6, role="harmony", aliases=("harpsichord",)),
    _I("organ", "Organ", "keyboards", 36, 96, 19, role="harmony", aliases=("organ",)),
    _I("guitar", "Guitar", "keyboards", 40, 88, 24, role="harmony", aliases=("guitar",)),
    # Voices
    _I("soprano", "Soprano", "voices", 60, 81, 52, role="melody", aliases=("soprano",)),
    _I("alto", "Alto", "voices", 53, 74, 52, role="harmony", aliases=("alto voice", "contralto")),
    _I("tenor", "Tenor", "voices", 48, 69, 52, role="harmony", aliases=("tenor",)),
    _I("bass_voice", "Bass voice", "voices", 40, 64, 52, role="bass", aliases=("bass voice", "baritone")),
    _I("choir", "Choir (SATB)", "voices", 48, 79, 52, role="harmony",
       aliases=("choir", "satb", "choral", "voices")),
    _I("rap_voice", "Rap / spoken voice", "voices", 45, 65, 85, role="melody", aliases=("rap", "spoken word")),
    # World / Indian
    _I("sitar", "Sitar", "world", 48, 84, 104, role="melody", aliases=("sitar",)),
    _I("bansuri", "Bansuri", "world", 60, 88, 75, role="melody", aliases=("bansuri",)),
    _I("shehnai", "Shehnai", "world", 58, 84, 111, role="melody", aliases=("shehnai",)),
    _I("santoor", "Santoor", "world", 48, 84, 15, role="colour", aliases=("santoor",)),
    _I("harmonium", "Harmonium", "world", 48, 84, 20, role="harmony", aliases=("harmonium",)),
    _I("tabla", "Tabla", "world", drum_notes=(60, 61, 62), role="rhythm", aliases=("tabla",)),
    _I("dhol", "Dhol", "world", drum_notes=(41, 64), role="rhythm", aliases=("dhol", "dholak")),
    # Electronic / hybrid
    _I("synth_pad", "Synth pad", "electronic", 36, 96, 89, role="harmony", aliases=("synth", "pad", "synth pad")),
    _I("sub_bass", "Sub bass", "electronic", 24, 55, 38, role="bass", aliases=("sub bass", "808")),
    _I("trailer_perc", "Trailer percussion", "electronic", drum_notes=(36, 39), role="rhythm",
       aliases=("hybrid percussion", "braams", "trailer drums")),
]}

# Default instruments used when a whole family is requested without naming instruments.
FAMILY_DEFAULTS = {
    "strings": ["violin", "viola", "cello", "double_bass"],
    "woodwinds": ["flute", "oboe", "clarinet", "bassoon"],
    "brass": ["horn", "trumpet", "trombone", "tuba"],
    "percussion": ["timpani", "bass_drum", "cymbals"],
    "keyboards": ["harp", "celesta"],
    "voices": ["choir"],
    "world": ["sitar", "tabla", "bansuri"],
    "electronic": ["synth_pad", "sub_bass", "trailer_perc"],
}

# Words that request a whole family.
FAMILY_WORDS = {
    "strings": ("strings", "string orchestra", "string section", "string quartet"),
    "woodwinds": ("woodwinds", "woodwind", "winds"),
    "brass": ("brass",),
    "percussion": ("percussion", "drums"),
    "keyboards": ("keyboards",),
    "voices": ("vocals", "singer", "singers", "vocal", "voice"),
    "world": ("indian instruments", "indian classical"),
    "electronic": ("electronic", "hybrid"),
}

# Ensemble words -> families they imply.
ENSEMBLES = {
    "full symphony orchestra": ["strings", "woodwinds", "brass", "percussion"],
    "symphony orchestra": ["strings", "woodwinds", "brass", "percussion"],
    "full orchestra": ["strings", "woodwinds", "brass", "percussion"],
    "chamber orchestra": ["strings", "woodwinds", "brass"],
    "string orchestra": ["strings"],
    "string quartet": ["strings"],
    "wind band": ["woodwinds", "brass", "percussion"],
    "brass band": ["brass", "percussion"],
    "wind quintet": ["woodwinds", "brass"],
    "orchestra": ["strings", "woodwinds", "brass", "percussion"],
}

STRING_QUARTET = ["violin", "violin", "viola", "cello"]


def instruments_of(family: str) -> list[Instrument]:
    return [i for i in INSTRUMENTS.values() if i.family == family]
