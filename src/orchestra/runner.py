# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""The study runner: generate every (request, generator, condition, seed), evaluate,
test the preregistered hypotheses, and write reports, manifests and SHA-256 sums."""
from __future__ import annotations

import gc
import json
import math
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .clap import frechet_distance
from .compiler import compile_prompt
from .conductor import conduct, plan_sections, sections_to_dicts
from .evaluate import Evaluator, calibrated_clarity
from .generators import make_generator
from .intent import parse_request, family_f1
from .orchestrator import orchestrate
from .provenance import base_manifest, now_iso, sha256_file, sha256_text, write_json, write_sums
from .report import write_reports
from .rights import rights_from_config, stamp, write_output_licence
from .stats import CONFIRMATORY_METRICS, SECONDARY_METRICS, agreement, run_tests


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def resolve_plan(cfg: dict, mode: str, overrides: dict) -> dict:
    s = cfg["study"]
    plan = {
        "mode": mode,
        "duration_s": float(s["duration_s"]),
        "seeds": list(s["seeds"]),
        "conditions": list(s["conditions"]),
        "generators": [g for g, gc_ in s["generators"].items() if gc_.get("enabled")],
        "request_ids": None,
        "metrics": s["metrics"],
        "strict": mode == "full",
    }
    if mode == "quick":
        q = cfg["quick"]
        plan.update({"duration_s": float(q["duration_s"]), "seeds": list(q["seeds"]),
                     "generators": list(q["generators"]), "request_ids": list(q["requests"]),
                     "metrics": {**s["metrics"], **{k: v for k, v in q["metrics"].items()}}})
        for k in ("clap", "judge", "fad"):
            if q["metrics"].get(k) is False:
                plan["metrics"][k] = {"enabled": False}
    for key in ("generators", "seeds", "request_ids"):
        if overrides.get(key):
            plan[key] = overrides[key]
    if overrides.get("duration_s"):
        plan["duration_s"] = float(overrides["duration_s"])
    if overrides.get("no_judge"):
        plan["metrics"] = {**plan["metrics"], "judge": {"enabled": False}}
    if overrides.get("allow_missing"):
        plan["strict"] = False
    return plan


def run_study(root: Path, config_path: Path, mode: str = "quick", out_dir: Path | None = None,
              overrides: dict | None = None, resume: str | None = None, log=print) -> Path:
    root = Path(root)
    overrides = overrides or {}
    cfg_text = Path(config_path).read_text(encoding="utf-8")
    cfg = yaml.safe_load(cfg_text)
    req_path = root / cfg["study"]["requests_file"]
    req_text = req_path.read_text(encoding="utf-8")
    requests = yaml.safe_load(req_text)["requests"]
    plan = resolve_plan(cfg, mode, overrides)
    if plan["request_ids"]:
        requests = [r for r in requests if r["id"] in plan["request_ids"]]
    gen_cfgs = cfg["study"]["generators"]
    rights = rights_from_config(cfg)
    rights["purpose"] = "explore"  # study runs are research, never cleared for release

    out_root = Path(out_dir or root / "results")
    if resume:
        run_dir = out_root / resume
        run_id = resume
    else:
        when = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_id = f"{when}_{mode}_{sha256_text(cfg_text)[:8]}"
        run_dir = out_root / run_id
    for sub in ("audio", "specs", "prompts", "tables", "logs"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    log_file = open(run_dir / "logs" / "run.log", "a", encoding="utf-8")

    def say(msg: str):
        line = f"{now_iso()} {msg}"
        log(line)
        log_file.write(line + "\n")
        log_file.flush()

    manifest = base_manifest("study", cfg, sha256_text(cfg_text), {
        "run_id": run_id, "mode": mode, "resolved_plan": plan,
        "requests_file": str(cfg["study"]["requests_file"]), "requests_sha256": sha256_text(req_text),
        "human_participants": False, "output_rights": rights})
    say(f"run {run_id}: {len(requests)} requests, generators={plan['generators']}, seeds={plan['seeds']}, "
        f"duration={plan['duration_s']}s")

    # ---- Stage 1-3 for every request, plus the target plan used for scoring.
    specs = {}
    parser_rows = []
    for r in requests:
        spec = parse_request(r["id"], r["text"])
        orch = orchestrate(spec)
        t = r["targets"]
        target_sections = plan_sections(t["form"], t["shape"], t["families"], plan["duration_s"], spec.tempo)
        specs[r["id"]] = (spec, orch, target_sections)
        write_json(run_dir / "specs" / f"{r['id']}.json", {
            "request": r, "spec": spec.to_dict(), "orchestration": orch.to_dict(),
            "conductor_plan": sections_to_dicts(conduct(spec, plan["duration_s"])),
            "target_plan": sections_to_dicts(target_sections)})
        parser_rows.append({"request_id": r["id"], "family_f1": family_f1(spec.families, t["families"]),
                            "form_correct": spec.form == t["form"], "shape_correct": spec.dynamics_shape == t["shape"]})
    pd.DataFrame(parser_rows).to_csv(run_dir / "tables" / "parser_accuracy.csv", index=False)
    heldout_rows = []
    ho_file = root / cfg["study"].get("heldout_requests_file", "config/heldout_requests.yaml")
    if ho_file.exists():
        ho = (yaml.safe_load(ho_file.read_text(encoding="utf-8")) or {}).get("requests") or []
        for r in ho:
            spec = parse_request(r["id"], r["text"])
            t = r["targets"]
            heldout_rows.append({"request_id": r["id"], "family_f1": family_f1(spec.families, t["families"]),
                                 "form_correct": spec.form == t["form"],
                                 "shape_correct": spec.dynamics_shape == t["shape"]})
        manifest["heldout_requests_sha256"] = sha256_file(ho_file)
    pd.DataFrame(heldout_rows).to_csv(run_dir / "tables" / "parser_accuracy_heldout.csv", index=False)

    # ---- Generation (resumable).
    rec_path = run_dir / "pieces.jsonl"
    done = {}
    if rec_path.exists():
        for line in rec_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("status") == "ok":
                done[rec["piece_id"]] = rec
    generator_info = {}
    for gname in plan["generators"]:
        gcfg = gen_cfgs.get(gname, {})
        try:
            gen = make_generator(gname, gcfg.get("options", {}))
        except Exception as e:
            if plan["strict"] and gname != "suno":
                raise
            say(f"[skip] generator {gname} unavailable: {e}")
            continue
        generator_info[gname] = gen.info()
        conds = [c for c in plan["conditions"] if c in gen.conditions]
        (run_dir / "audio" / gname).mkdir(exist_ok=True)
        for r in requests:
            spec, orch, _ = specs[r["id"]]
            sections = conduct(spec, plan["duration_s"])
            for cond in conds:
                prompt = compile_prompt(cond, spec, orch, sections, gcfg.get("max_prompt_words", 90))
                for seed in plan["seeds"]:
                    pid = f"{gname}__{r['id']}__{cond}__s{seed}"
                    wav = run_dir / "audio" / gname / f"{r['id']}_{cond}_s{seed}.wav"
                    if pid in done and wav.exists() and sha256_file(wav) == done[pid]["audio_sha256"]:
                        continue
                    (run_dir / "prompts" / f"{pid}.txt").write_text(prompt, encoding="utf-8")
                    rec = {"piece_id": pid, "generator": gname, "request_id": r["id"], "condition": cond,
                           "seed": seed, "prompt": prompt, "prompt_sha256": sha256_text(prompt),
                           "reproducible": bool(getattr(gen, "reproducible", True)), "started_utc": now_iso()}
                    t0 = time.time()
                    try:
                        info = gen.generate(condition=cond, prompt=prompt, seed=seed, duration=plan["duration_s"],
                                            out_wav=wav, spec=spec, plan=orch, sections=sections)
                        stamp(wav, rights, title=pid)
                        rec.update({"status": "ok", "audio_file": wav.relative_to(run_dir).as_posix(),
                                    "audio_sha256": sha256_file(wav), "generator_info": info})
                    except Exception as e:
                        rec.update({"status": "error", "error": repr(e), "trace": traceback.format_exc()[-2000:]})
                        say(f"[error] {pid}: {e!r}")
                    rec["seconds"] = round(time.time() - t0, 2)
                    with open(rec_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec, default=str) + "\n")
                    if rec["status"] == "ok":
                        done[pid] = rec
                        say(f"generated {pid} in {rec['seconds']}s")
        del gen
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass

    # ---- Evaluation.
    evaluator = Evaluator(plan["metrics"], strict=plan["strict"], log=say)
    rows, embs = [], {}
    targets = {r["id"]: r["targets"] for r in requests}
    texts = {r["id"]: r["text"] for r in requests}
    for pid, rec in sorted(done.items()):
        if rec["generator"] not in plan["generators"] or rec["request_id"] not in targets:
            continue
        _, _, target_sections = specs[rec["request_id"]]
        t = targets[rec["request_id"]]
        m, emb = evaluator.evaluate(run_dir / rec["audio_file"], texts[rec["request_id"]], target_sections,
                                    t["families"], plan["duration_s"], t.get("culture"))
        gi = rec.get("generator_info", {})
        rows.append({"piece_id": pid, "generator": rec["generator"], "request_id": rec["request_id"],
                     "condition": rec["condition"], "seed": rec["seed"], "reproducible": rec["reproducible"],
                     "audio_sha256": rec["audio_sha256"], "range_violations": gi.get("range_violations"),
                     "range_repairs": gi.get("range_repairs"), **m})
        if emb is not None:
            embs[pid] = emb
        say(f"evaluated {pid}")
    pieces = pd.DataFrame(rows)
    if pieces.empty:
        raise RuntimeError("no pieces were generated; see logs/run.log")
    pieces = calibrated_clarity(pieces, {k: v["families"] for k, v in targets.items()})
    pieces.to_csv(run_dir / "tables" / "pieces.csv", index=False)

    # ---- FAD per generator x condition against real recordings (descriptive).
    fad_rows = []
    fad_cfg = plan["metrics"].get("fad", {})
    ref_dir = root / fad_cfg.get("reference_dir", "data/reference_orchestral") if isinstance(fad_cfg, dict) else None
    if evaluator.clap and isinstance(fad_cfg, dict) and fad_cfg.get("enabled") and ref_dir and ref_dir.exists():
        refs = sorted([p for p in ref_dir.rglob("*") if p.suffix.lower() in (".wav", ".flac", ".mp3", ".ogg")])
        ref_emb = np.stack([evaluator.clap.embed_audio_file(p) for p in refs]) if refs else None
        manifest["fad_reference"] = {"dir": str(fad_cfg.get("reference_dir")), "files": len(refs),
                                     "sha256": {p.name: sha256_file(p) for p in refs}}
        if ref_emb is not None:
            for (g, c), sub in pieces.groupby(["generator", "condition"]):
                e = np.stack([embs[p] for p in sub["piece_id"] if p in embs])
                fad_rows.append({"generator": g, "condition": c, "n": len(e), "n_reference": len(refs),
                                 "fad_clap": frechet_distance(e, ref_emb)})
    elif isinstance(fad_cfg, dict) and fad_cfg.get("enabled"):
        say("[skip] FAD: add real orchestral recordings to the reference folder to compute it")
    pd.DataFrame(fad_rows).to_csv(run_dir / "tables" / "fad.csv", index=False)

    # ---- Statistics (confirmatory set excludes non-reproducible generators).
    metric_cols = [c for c in pieces.columns if c in CONFIRMATORY_METRICS + SECONDARY_METRICS
                   or c.startswith("judge_") and c not in ("judge_advice", "judge_raw")]
    per_request = (pieces.groupby(["generator", "request_id", "condition"])[metric_cols]
                   .mean(numeric_only=True).reset_index())
    per_request.to_csv(run_dir / "tables" / "per_request.csv", index=False)
    st = cfg["study"]["stats"]
    repro = per_request[per_request["generator"] != "suno"]
    conf = run_tests(repro, [tuple(c) for c in st["confirmatory_comparisons"]],
                     [m for m in CONFIRMATORY_METRICS if m in repro], "confirmatory",
                     st["bootstrap_resamples"], st["bootstrap_seed"], st["alpha"])
    sec_metrics = [m for m in CONFIRMATORY_METRICS + SECONDARY_METRICS + ["judge_overall"] if m in per_request]
    sec = run_tests(per_request, [tuple(c) for c in st["secondary_comparisons"]], list(dict.fromkeys(sec_metrics)),
                    "secondary", st["bootstrap_resamples"], st["bootstrap_seed"], st["alpha"])
    sec_extra = run_tests(per_request, [tuple(c) for c in st["confirmatory_comparisons"]],
                          [m for m in SECONDARY_METRICS + ["judge_overall"] if m in per_request], "secondary",
                          st["bootstrap_resamples"], st["bootstrap_seed"], st["alpha"])
    stats_df = pd.concat([conf, sec, sec_extra], ignore_index=True)
    stats_df.to_csv(run_dir / "tables" / "hypothesis_tests.csv", index=False)
    agree = agreement(pieces, CONFIRMATORY_METRICS + ["judge_overall", "judge_adherence", "judge_orchestration",
                                                      "judge_dynamics", "judge_structure"])
    agree.to_csv(run_dir / "tables" / "measure_agreement.csv", index=False)
    summary = (pieces.groupby(["generator", "condition"])[[c for c in metric_cols if c in pieces]]
               .agg(["mean", "std", "count"]))
    summary.columns = [f"{a}_{b}" for a, b in summary.columns]
    summary.reset_index().to_csv(run_dir / "tables" / "summary.csv", index=False)

    # ---- Manifest, reports, hashes.
    manifest.update({"finished_utc": now_iso(), "generators": generator_info, "evaluator": evaluator.info(),
                     "n_pieces_ok": int(len(pieces)),
                     "n_pieces_failed": sum(1 for l in rec_path.read_text().splitlines()
                                            if json.loads(l).get("status") != "ok") if rec_path.exists() else 0})
    write_json(run_dir / "manifest.json", manifest)
    write_output_licence(run_dir, rights, [i.get("model", g) for g, i in generator_info.items()])
    write_reports(run_dir, manifest, pieces, stats_df, agree, pd.DataFrame(parser_rows), pd.DataFrame(fad_rows),
                  pd.DataFrame(heldout_rows))
    log_file.close()
    write_sums(run_dir)
    (out_root / "LATEST").write_text(run_id + "\n", encoding="utf-8")
    log(f"done: {run_dir}")
    return run_dir
