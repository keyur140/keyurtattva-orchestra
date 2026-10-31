# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Credit and rights notices embedded in every generated file.

Every WAV gets a RIFF INFO chunk (artist, copyright, licence, software), every MIDI file a
copyright meta event, and every output folder an OUTPUT_LICENSE.md. Embedding happens
before hashing, so the SHA-256 hashes cover the notices too.

Important: a notice states a claim and a licence; it cannot create copyright where the law
gives none, and it cannot override the terms of the AI model that produced the audio.
See docs/IMPACT.md, section "Copyright, credit and royalties".
"""
from __future__ import annotations

import struct
from datetime import datetime, timezone
from pathlib import Path

from . import AUTHOR, __version__

LICENCES = {
    "CC-BY-4.0": ("Creative Commons Attribution 4.0 International",
                  "https://creativecommons.org/licenses/by/4.0/"),
    "CC-BY-NC-4.0": ("Creative Commons Attribution-NonCommercial 4.0 International",
                     "https://creativecommons.org/licenses/by-nc/4.0/"),
    "ARR": ("All rights reserved", ""),
}

DEFAULT_RIGHTS = {
    "artist": "KeyurTattva",
    "owner": AUTHOR["name"],
    "licence": "CC-BY-NC-4.0",
    "credit_line": "Music by KeyurTattva (KEYUR SHAILESHKUMAR PATEL)",
    "commercial_contact": "via the author's ORCID profile: https://orcid.org/0009-0008-5261-043X",
}


def rights_from_config(cfg: dict) -> dict:
    r = dict(DEFAULT_RIGHTS)
    r.update((cfg or {}).get("output_rights") or {})
    if r["licence"] not in LICENCES:
        raise ValueError(f"output_rights.licence must be one of {list(LICENCES)}")
    return r


def copyright_line(r: dict) -> str:
    year = datetime.now(timezone.utc).year
    name, url = LICENCES[r["licence"]]
    lic = f"{name} ({url})" if url else name
    return f"(c) {year} {r['owner']} ({r['artist']}). {lic}. Credit required: \"{r['credit_line']}\"."


def _info_chunk(fields: dict[str, str]) -> bytes:
    body = b"INFO"
    for key, value in fields.items():
        data = value.encode("utf-8") + b"\x00"
        if len(data) % 2:
            data += b"\x00"
        body += key.encode("ascii") + struct.pack("<I", len(data)) + data
    return b"LIST" + struct.pack("<I", len(body)) + body


def _purpose_note(r: dict) -> str:
    if r.get("purpose") == "publish":
        return f"Tattva publish mode: cleared via {r.get('cleared_via', 'the publish policy')}."
    return "Exploration output - not cleared for release."


def stamp_wav(path, r: dict, title: str = "") -> None:
    """Append (or replace) the RIFF INFO chunk with artist, copyright and licence notices."""
    p = Path(path)
    raw = p.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        return
    # Rebuild the file without any existing LIST/INFO chunk.
    chunks, pos = [], 12
    while pos + 8 <= len(raw):
        cid, size = raw[pos:pos + 4], struct.unpack("<I", raw[pos + 4:pos + 8])[0]
        end = pos + 8 + size + (size % 2)
        if not (cid == b"LIST" and raw[pos + 8:pos + 12] == b"INFO"):
            chunks.append(raw[pos:end])
        pos = end
    info = _info_chunk({
        "INAM": title or p.stem,
        "IART": r["artist"],
        "ICOP": copyright_line(r),
        "ICMT": f"Credit: {r['credit_line']}. Commercial licences {r['commercial_contact']}. "
                f"Generated with AI models; their own terms also apply. " + _purpose_note(r),
        "ISFT": f"Orchestral Input Pipeline {__version__}",
        "ICRD": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    })
    body = b"WAVE" + b"".join(chunks) + info
    p.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)


def stamp_midi(path, r: dict) -> None:
    try:
        import mido
    except ImportError:
        return
    mid = mido.MidiFile(str(path))
    if mid.tracks:
        track = mid.tracks[0]
        track[:] = [m for m in track if not (m.is_meta and m.type in ("copyright", "text"))]
        track.insert(0, mido.MetaMessage("copyright", text=copyright_line(r)[:250], time=0))
        track.insert(1, mido.MetaMessage("text", text=f"Artist: {r['artist']}", time=0))
        mid.save(str(path))


def stamp(wav_path, r: dict, title: str = "") -> None:
    stamp_wav(wav_path, r, title)
    mid = Path(wav_path).with_suffix(".mid")
    if mid.exists():
        stamp_midi(mid, r)


def write_output_licence(folder, r: dict, models: list[str]) -> Path:
    name, url = LICENCES[r["licence"]]
    terms = {
        "CC-BY-4.0": "Anyone may use, share, adapt and sell this music, as long as they give credit.",
        "CC-BY-NC-4.0": "Anyone may use, share and adapt this music for non-commercial purposes, as long as "
                        f"they give credit. Commercial use needs a separate licence: contact {r['commercial_contact']}.",
        "ARR": f"No reuse without written permission. Contact {r['commercial_contact']}.",
    }[r["licence"]]
    text = f"""# Output licence and credit

**Artist:** {r['artist']}
**Owner:** {r['owner']} (ORCID {AUTHOR['orcid']})
**Notice:** {copyright_line(r)}

## Licence
{name}{(' - ' + url) if url else ''}

{terms}

## Required credit
> {r['credit_line']}

## Purpose
{"**Tattva publish mode.** Made only with a route cleared for release (" + r.get("cleared_via", "") + "). See RELEASE_CHECKLIST.md." if r.get("purpose") == "publish" else "**Explore mode: not cleared for release.** It may use research-only models. Remake it with `--purpose publish` before you release anything."}

## Also applies
This audio was generated with: {', '.join(models) or 'the models listed in manifest.json'}.
Those models' own licences and terms also apply and may restrict commercial use.
Copyright in AI-generated material depends on the country and on the human contribution.
This notice states the owner's claim and licence; it is not legal advice.
"""
    out = Path(folder) / "OUTPUT_LICENSE.md"
    out.write_text(text, encoding="utf-8")
    return out
