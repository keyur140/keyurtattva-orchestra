# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Run reports in Markdown, HTML and PDF."""
from __future__ import annotations

import html
import math
from pathlib import Path

import pandas as pd

from . import AUTHOR, PROJECT_TITLE

LIMITATIONS = [
    "All measures are automatic proxies for musical quality; no human listeners were involved.",
    "The AI judge is itself a model with its own biases; it is reported as a secondary measure only.",
    "CLAP similarities depend on the CLAP model's training data, which under-represents some styles "
    "(for example Indian classical music).",
    "Pieces are short (default 30 s), so large-scale form is tested only in compressed form.",
    "The intent parser was developed alongside the main benchmark; its accuracy there is optimistic. "
    "Parser accuracy on the held-out requests is the fair estimate.",
    "Closed services (Suno) cannot be re-run exactly and are excluded from confirmatory tests.",
]


def _fmt(v) -> str:
    if isinstance(v, float):
        if math.isnan(v):
            return "-"
        return f"{v:.3g}" if abs(v) < 1e-3 and v != 0 else f"{v:.3f}"
    return str(v)


def _md_table(df: pd.DataFrame, cols: list[str] | None = None) -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    cols = [c for c in (cols or list(df.columns)) if c in df]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df[cols].iterrows():
        lines.append("| " + " | ".join(_fmt(r[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def _sentences(tests: pd.DataFrame) -> list[str]:
    out = []
    if tests is None or tests.empty:
        return ["No hypothesis tests could be run (too few pieces or measures)."]
    conf = tests[tests["family"] == "confirmatory"]
    for _, r in conf.iterrows():
        a, b = r["comparison"].split(" vs ")
        if not math.isfinite(r.get("p_holm", math.nan)):
            out.append(f"{r['generator']}: {r['metric']} could not be tested ({int(r['n_pairs'])} pairs; the test needs at least 6).")
            continue
        direction = "higher" if r["median_diff"] > 0 else "lower" if r["median_diff"] < 0 else "equal"
        verdict = "a statistically significant difference" if r["significant"] else "no significant difference"
        out.append(f"{r['generator']}: the {a} condition scored {direction} than {b} on {r['metric']} "
                   f"(median difference {_fmt(r['median_diff'])}, 95% CI {_fmt(r['ci95_low'])} to "
                   f"{_fmt(r['ci95_high'])}, Holm-adjusted p = {_fmt(r['p_holm'])}, effect size r = "
                   f"{_fmt(r['rank_biserial'])}, {int(r['n_pairs'])} requests): {verdict}.")
    return out


def build_markdown(manifest: dict, pieces, tests, agree, parser, fad, heldout=None) -> str:
    mode = manifest.get("mode")
    key = [c for c in ["prompt_adherence", "section_clarity", "dynamics_accuracy", "structure_f",
                       "structure_chance", "judge_overall", "dynamic_range_db", "range_violations"] if c in pieces]
    means = pieces.groupby(["generator", "condition"])[key].mean(numeric_only=True).reset_index()
    parts = [f"# Run report: {PROJECT_TITLE}", ""]
    if mode == "quick":
        parts += ["> **Smoke test only.** Quick mode checks that the package works. Its numbers are not "
                  "study results and must not be reported as findings.", ""]
    parts += [
        f"**Author:** {AUTHOR['name']} (ORCID {AUTHOR['orcid']})  ",
        f"**Affiliations:** (1) {AUTHOR['affiliations'][0]}; (2) {AUTHOR['affiliations'][1]}  ",
        f"*{AUTHOR['note']}*", "",
        f"- Run: `{manifest['run_id']}` ({mode} mode)",
        f"- Started {manifest['started_utc']}, finished {manifest.get('finished_utc')}",
        f"- Config SHA-256: `{manifest['config_sha256']}`",
        f"- Requests SHA-256: `{manifest.get('requests_sha256')}`",
        f"- Pieces evaluated: {manifest.get('n_pieces_ok')} (failed: {manifest.get('n_pieces_failed')})",
        "- Human participants: none (fully computational study)",
        "- Every file in this folder is listed with its SHA-256 hash in `SHA256SUMS`.", "",
        "## Results in plain words", ""]
    parts += [f"- {s}" for s in _sentences(tests)]
    parts += ["", "## Mean scores by generator and condition", "", _md_table(means),
              "`structure_chance` is the boundary score expected from random boundaries; "
              "`structure_f` should be read against it.", "",
              "## Confirmatory tests (preregistered)", "",
              _md_table(tests[tests["family"] == "confirmatory"] if not tests.empty else tests),
              "## Secondary tests", "",
              _md_table(tests[tests["family"] == "secondary"] if not tests.empty else tests),
              "## Agreement between measures (Spearman)", "", _md_table(agree),
              "## Intent-parser accuracy on the benchmark", "",
              f"Mean family F1 {_fmt(parser['family_f1'].mean())}, form correct "
              f"{int(parser['form_correct'].sum())}/{len(parser)}, dynamic shape correct "
              f"{int(parser['shape_correct'].sum())}/{len(parser)} (optimistic: rules were written with these requests).",
              "",
              ("Held-out requests: mean family F1 " + _fmt(heldout["family_f1"].mean()) + ", form correct "
               + f"{int(heldout['form_correct'].sum())}/{len(heldout)}, shape correct "
               + f"{int(heldout['shape_correct'].sum())}/{len(heldout)}."
               if heldout is not None and not heldout.empty else
               "Held-out requests: none yet (add them to config/heldout_requests.yaml before the main run)."), "",
              "## Frechet Audio Distance (CLAP embeddings, lower is closer to real recordings)", "",
              _md_table(fad), "## Limitations", ""]
    parts += [f"- {x}" for x in LIMITATIONS]
    parts += ["", "## Reproduce and verify", "",
              "```", "python run_all.py verify results/" + manifest["run_id"], "```", ""]
    return "\n".join(parts)


def _md_to_html(md: str, title: str) -> str:
    body, in_table, in_code, in_list = [], False, False, False
    for line in md.splitlines():
        if line.startswith("```"):
            body.append("</pre>" if in_code else "<pre>")
            in_code = not in_code
            continue
        if in_code:
            body.append(html.escape(line))
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= {"-"} for c in cells):
                continue
            tag = "th" if not in_table else "td"
            if not in_table:
                body.append("<table>")
                in_table = True
            body.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            body.append("</table>")
            in_table = False
        if line.startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{html.escape(line[2:])}</li>")
            continue
        if in_list:
            body.append("</ul>")
            in_list = False
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("> "):
            body.append(f"<blockquote>{html.escape(line[2:]).replace('**', '')}</blockquote>")
        elif line.strip():
            body.append(f"<p>{html.escape(line).replace('**', '')}</p>")
    if in_table:
        body.append("</table>")
    if in_list:
        body.append("</ul>")
    css = ("body{font-family:system-ui,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;color:#222}"
           "table{border-collapse:collapse;font-size:13px;margin:1em 0;display:block;overflow-x:auto}"
           "td,th{border:1px solid #ccc;padding:4px 8px;text-align:left}th{background:#f2f2f2}"
           "blockquote{background:#fff4d6;padding:8px 12px;border-left:4px solid #e0a800}pre{background:#f6f6f6;padding:8px}")
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            f"<style>{css}</style></head><body>{''.join(body)}</body></html>")


def _pdf(md: str, path: Path) -> None:
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except ImportError:
        return
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=36, rightMargin=36,
                            title="Run report", author=AUTHOR["name"])
    story, rows = [], []

    def flush():
        nonlocal rows
        if rows:
            small = [[Paragraph(html.escape(c), styles["BodyText"]) for c in r] for r in rows]
            t = Table(small, repeatRows=1)
            t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                                   ("FONTSIZE", (0, 0), (-1, -1), 6)]))
            story.append(t)
            story.append(Spacer(1, 8))
            rows = []

    for line in md.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(set(c) <= {"-"} for c in cells):
                rows.append(cells)
            continue
        flush()
        if line.startswith("```") or not line.strip():
            continue
        text = html.escape(line.lstrip("#> -").strip()).replace("**", "").replace("`", "")
        style = "Title" if line.startswith("# ") else "Heading2" if line.startswith("## ") else "BodyText"
        story.append(Paragraph(text, styles[style]))
    flush()
    doc.build(story)


def write_reports(run_dir: Path, manifest: dict, pieces, tests, agree, parser, fad, heldout=None) -> None:
    md = build_markdown(manifest, pieces, tests, agree, parser, fad, heldout)
    (run_dir / "report.md").write_text(md, encoding="utf-8")
    (run_dir / "report.html").write_text(_md_to_html(md, f"Run report {manifest['run_id']}"), encoding="utf-8")
    _pdf(md, run_dir / "report.pdf")
