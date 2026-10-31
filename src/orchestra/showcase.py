# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""KeyurTattva showcase: make the author's own songs after every run, as visible proof.

The song list is ``config/showcase.yaml``. Each song goes through song mode (plan, generate,
measure, keep-best refinement). The results are demonstrations only and never enter the
preregistered analysis. A ``SHOWCASE.md`` index and a ``SHA256SUMS`` file cover the whole set.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from .provenance import write_sums
from .song import run_song


def load_showcase(root: Path) -> dict:
    path = Path(root) / "config" / "showcase.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def run_showcase(root: Path, config_path: Path, mode: str = "quick", out_dir: Path | None = None,
                 only: list[str] | None = None, generator: str | None = None, versions: int | None = None,
                 duration: float | None = None, log=print) -> Path | None:
    """Make the showcase songs for ``mode`` (quick or full). Returns the showcase folder."""
    root = Path(root)
    sc = load_showcase(root)
    if not sc.get("songs"):
        log("[showcase] no config/showcase.yaml songs; skipped")
        return None
    plan = sc.get(mode) or sc.get("quick") or {}
    wanted = only or plan.get("songs", "all")
    songs = sc["songs"] if wanted == "all" else [s for s in sc["songs"] if s["id"] in set(wanted)]
    when = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    show_dir = Path(out_dir or root / "songs") / f"showcase_{when}_{mode}"
    show_dir.mkdir(parents=True, exist_ok=True)
    gen = generator or plan.get("generator")
    log(f"[showcase] making {len(songs)} KeyurTattva song(s) in {show_dir} (demonstration, not analysed)")

    rows = []
    for s in songs:
        try:
            folder = run_song(root, config_path, s["request"], generator=gen,
                              versions=versions or plan.get("versions"), duration=duration or plan.get("duration_s"),
                              out_dir=show_dir, log=lambda m, i=s["id"]: log(f"[showcase {i}] {m}"),
                              purpose="explore")
            df = pd.read_csv(folder / "versions.csv")
            best = (folder / "BEST.txt").read_text(encoding="utf-8").strip()
            row = df.loc[df["score"].idxmax()] if df["score"].notna().any() else df.iloc[-1]
            rows.append({"id": s["id"], "title": s["title"], "status": "ok", "best": best,
                         "score": round(float(row["score"]), 3) if pd.notna(row["score"]) else None,
                         "folder": folder.name})
        except Exception as e:  # one failed song never stops the others
            log(f"[showcase {s['id']}] failed: {e}")
            rows.append({"id": s["id"], "title": s["title"], "status": f"failed: {e}"[:120],
                         "best": "", "score": None, "folder": ""})

    lines = ["# KeyurTattva showcase", "",
             f"Made {when} UTC after a {mode} run. Generator: {gen or 'song default'}. "
             "These songs are demonstrations of the pipeline on the author's own song descriptions. "
             "They are not part of the preregistered analysis. Files are marked "
             "\"Exploration output - not cleared for release\".", "",
             "| Song | Status | Best version | Score (0-1) | Folder |", "| --- | --- | --- | --- | --- |"]
    for r in rows:
        score = "" if r["score"] is None else f"{r['score']:.3f}"
        lines.append(f"| {r['id']} {r['title']} | {r['status']} | {r['best']} | {score} | {r['folder']} |")
    lines += ["", "Music by KeyurTattva (KEYUR SHAILESHKUMAR PATEL). Check every file with "
              f"`python run_all.py verify {show_dir.relative_to(root) if show_dir.is_relative_to(root) else show_dir}`."]
    (show_dir / "SHOWCASE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(show_dir / "showcase.csv", index=False)
    write_sums(show_dir)
    ok = sum(r["status"] == "ok" for r in rows)
    log(f"[showcase] done: {ok}/{len(rows)} songs made, index in {show_dir / 'SHOWCASE.md'}")
    return show_dir
