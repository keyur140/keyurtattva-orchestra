# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Generator registry. Heavy libraries are imported only when a generator is created."""
from __future__ import annotations


def make_generator(name: str, options: dict | None = None):
    options = dict(options or {})
    if name == "midi":
        from .midi import MidiGenerator
        return MidiGenerator(**options)
    if name == "musicgen":
        from .text_to_audio import MusicGenGenerator
        return MusicGenGenerator(**options)
    if name == "musicgen_melody":
        from .text_to_audio import MusicGenMelodyGenerator
        return MusicGenMelodyGenerator(**options)
    if name == "stable_audio":
        from .text_to_audio import StableAudioGenerator
        return StableAudioGenerator(**options)
    if name == "suno":
        from .suno import SunoGenerator
        return SunoGenerator(**options)
    raise ValueError(f"unknown generator: {name}")


GENERATORS = ("midi", "musicgen", "stable_audio", "suno")
SONG_GENERATORS = GENERATORS + ("musicgen_melody",)  # song mode only: follows a sung tune
