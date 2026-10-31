# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Provenance: SHA-256 hashing of every file, SHA256SUMS files, and run manifests."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

from . import AUTHOR, PROJECT_TITLE, __version__

SUMS_NAME = "SHA256SUMS"
TRACKED_PACKAGES = ["numpy", "scipy", "pandas", "librosa", "soundfile", "pretty_midi", "PyYAML",
                    "reportlab", "torch", "transformers", "diffusers", "accelerate"]


def sha256_file(path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


SKIP_PARTS = {"__pycache__", ".pytest_cache", ".git"}
SKIP_FILES = {SUMS_NAME, ".env", "HUMAN_CONTRIBUTIONS.md"}  # the last one is yours to edit
# In the package folder itself, new runs, songs and your own lyric files are expected
# and are not part of the package.
PACKAGE_RUNTIME = ("results/", "songs/", "lyrics/")
PACKAGE_KEEP = ("results/README.md", "lyrics/README.md", "lyrics/example_song.txt",
                "lyrics/generated/.gitkeep")


def _files(root: Path):
    is_package = (root / "run_all.py").exists()
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name in SKIP_FILES or SKIP_PARTS & set(p.relative_to(root).parts):
            continue
        rel = p.relative_to(root).as_posix()
        if is_package and rel.startswith(PACKAGE_RUNTIME) and rel not in PACKAGE_KEEP:
            continue
        yield p, rel


def write_sums(root: Path) -> Path:
    """Hash every file under ``root`` (except the sums file) into ``root/SHA256SUMS``."""
    root = Path(root)
    lines = [f"{sha256_file(p)}  {rel}" for p, rel in _files(root)]
    out = root / SUMS_NAME
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def verify_sums(root: Path) -> tuple[int, list[str]]:
    """Return (files checked, problems). An empty problem list means everything matches."""
    root = Path(root)
    sums = root / SUMS_NAME
    if not sums.exists():
        return 0, [f"{SUMS_NAME} not found in {root}"]
    problems, n = [], 0
    for line in sums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        n += 1
        p = root / rel
        if not p.exists():
            problems.append(f"missing: {rel}")
        elif sha256_file(p) != digest:
            problems.append(f"changed: {rel}")
    listed = {line.split("  ", 1)[1] for line in sums.read_text(encoding="utf-8").splitlines() if line.strip()}
    for _, rel in _files(root):
        if rel not in listed:
            problems.append(f"not listed: {rel}")
    return n, problems


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def environment() -> dict:
    pkgs = {}
    for name in TRACKED_PACKAGES:
        try:
            pkgs[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pkgs[name] = None
    gpu = None
    try:
        import torch
        if torch.cuda.is_available():
            gpu = {"name": torch.cuda.get_device_name(0), "count": torch.cuda.device_count(),
                   "cuda": torch.version.cuda}
    except ImportError:
        pass
    return {"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine(),
            "processor": platform.processor() or None, "cpu_count": os.cpu_count(), "gpu": gpu,
            "packages": pkgs}


def base_manifest(kind: str, config: dict, config_sha: str, extra: dict | None = None) -> dict:
    m = {
        "manifest_version": 1,
        "kind": kind,
        "project": PROJECT_TITLE,
        "software_version": __version__,
        "author": AUTHOR,
        "licence": {"code": "MIT", "documents_and_data": "CC BY 4.0"},
        "started_utc": now_iso(),
        "config_sha256": config_sha,
        "config": config,
        "environment": environment(),
    }
    if extra:
        m.update(extra)
    return m


def write_json(path: Path, data) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
