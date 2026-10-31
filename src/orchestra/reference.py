# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Fetch the frozen FAD reference set (real orchestral recordings from MTG-Jamendo).

The list of tracks, their SHA-256 hashes and the hashes of the archives that hold them are
fixed in ``config/fad_reference.tsv``. This module downloads only the archives named there,
checks every hash, copies the listed tracks into ``data/reference_orchestral/`` and writes an
``ATTRIBUTION.md`` with each track's credit and Creative Commons licence.
"""
from __future__ import annotations

import shutil
import tarfile
import urllib.request
from pathlib import Path

from .provenance import sha256_file

SOURCES = {
    "mtg-fast": "https://cdn.freesound.org/mtg-jamendo/raw_30s/audio-low/",
    "mtg": "https://essentia.upf.edu/documentation/datasets/mtg-jamendo/raw_30s/audio-low/",
}


class ReferenceError(RuntimeError):
    pass


def read_list(path: Path) -> tuple[dict[str, str], list[dict]]:
    """Return ({archive name: sha256}, [track rows]) from the frozen TSV."""
    tars, rows, header = {}, [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# tar "):
            _, _, name, digest = line.split()
            tars[name] = digest
        elif line.startswith("#") or not line.strip():
            continue
        elif header is None:
            header = line.split("\t")
        else:
            rows.append(dict(zip(header, line.split("\t"))))
    if not tars or not rows:
        raise ReferenceError(f"{path} has no archives or no tracks")
    return tars, rows


def _archive_for(file: str, tars: dict[str, str]) -> str:
    folder = file.split("/")[0]
    for name in tars:
        if name.endswith(f"-{folder}.tar"):
            return name
    raise ReferenceError(f"no archive listed for {file}")


def _download(url: str, dest: Path, log) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    log(f"downloading {url}")
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:  # noqa: S310 (fixed https sources)
        total = int(r.headers.get("Content-Length") or 0)
        done, step = 0, 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total and done * 10 // total > step:
                step = done * 10 // total
                log(f"  {step * 10}% of {total / 1e9:.2f} GB")
    tmp.rename(dest)


def fetch_reference(root: Path, *, source: str = "mtg-fast", base_url: str | None = None,
                    keep_archives: bool = False, log=print) -> Path:
    """Download, verify and install the reference tracks. Returns the reference folder."""
    root = Path(root)
    tars, rows = read_list(root / "config" / "fad_reference.tsv")
    out = root / "data" / "reference_orchestral"
    cache = root / "data" / "cache"
    out.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    base = base_url or SOURCES[source]

    todo = [r for r in rows if not ((out / Path(r["file"]).name).exists()
                                    and sha256_file(out / Path(r["file"]).name) == r["sha256"])]
    for name in sorted({_archive_for(r["file"], tars) for r in todo}):
        archive = cache / name
        if not (archive.exists() and sha256_file(archive) == tars[name]):
            _download(base + name, archive, log)
            if sha256_file(archive) != tars[name]:
                archive.unlink()
                raise ReferenceError(f"{name}: SHA-256 does not match the frozen list; file removed")
        log(f"{name}: SHA-256 OK")
        wanted = {r["file"]: r for r in todo if _archive_for(r["file"], tars) == name}
        with tarfile.open(archive) as tf:
            for m in tf.getmembers():
                key = next((w for w in wanted if m.name.endswith(w)), None)
                if key is None or not m.isfile():
                    continue
                target = out / Path(key).name
                with tf.extractfile(m) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                if sha256_file(target) != wanted[key]["sha256"]:
                    target.unlink()
                    raise ReferenceError(f"{key}: SHA-256 does not match the frozen list")
        if not keep_archives:
            archive.unlink()

    missing = [r["file"] for r in rows if not (out / Path(r["file"]).name).exists()]
    if missing:
        raise ReferenceError(f"{len(missing)} tracks missing after download, e.g. {missing[0]}")
    lines = ["# Credits for the FAD reference recordings", "",
             "Source: MTG-Jamendo dataset (Bogdanov et al., 2019), https://github.com/MTG/mtg-jamendo-dataset.",
             "Used only to compute embeddings for a non-commercial research comparison. Not redistributed.", ""]
    lines += [f"- {r['file']}: {r['credit']}. Licence: {r['licence']}" for r in rows]
    (out / "ATTRIBUTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"done: {len(rows)} reference recordings in {out} (all SHA-256 checked)")
    return out
