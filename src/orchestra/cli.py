# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Command line: app | quick | full | song | spec | verify | check."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from . import AUTHOR, PROJECT_TITLE, __version__


def load_env(path: Path) -> list[str]:
    """Read KEY=VALUE lines from .env into the environment (existing variables win)."""
    loaded = []
    if not path.exists():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if v and k not in os.environ:
            os.environ[k] = v
            loaded.append(k)
    return loaded


def cmd_check(root: Path) -> int:
    print(f"{PROJECT_TITLE} v{__version__}\nAuthor: {AUTHOR['name']} ({AUTHOR['orcid']})\n")
    rows = []
    for mod, why in [("numpy", "core"), ("scipy", "core"), ("pandas", "core"), ("yaml", "core"),
                     ("librosa", "core metrics"), ("soundfile", "core audio"), ("pretty_midi", "MIDI route"),
                     ("reportlab", "PDF reports"), ("torch", "AI models"), ("transformers", "MusicGen, CLAP, judge, lyrics"),
                     ("diffusers", "Stable Audio Open"), ("accelerate", "large models on GPU")]:
        try:
            __import__(mod)
            rows.append((mod, "ok", why))
        except ImportError:
            rows.append((mod, "missing", why))
    for name, status, why in rows:
        print(f"  {name:13s} {status:8s} {why}")
    try:
        import torch
        print(f"\n  GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none (CPU only)'}")
    except ImportError:
        print("\n  GPU: unknown (torch not installed)")
    print(f"  fluidsynth: {'found' if shutil.which('fluidsynth') else 'not found (built-in synth used)'}")
    sf = os.environ.get("SOUNDFONT_PATH")
    print(f"  SOUNDFONT_PATH: {sf if sf and Path(sf).exists() else 'not set'}")
    print(f"  HF_TOKEN: {'set' if os.environ.get('HF_TOKEN') else 'not set (needed for Stable Audio Open)'}")
    print(f"  SUNO_API_KEY: {'set' if os.environ.get('SUNO_API_KEY') else 'not set (optional)'}")
    for key in ("SUNO_PAID_PLAN", "STABLE_AUDIO_LICENCE_ACCEPTED"):
        print(f"  {key}: {os.environ.get(key) or 'not declared (needed only for publish mode)'}")
    ref = root / "data" / "reference_orchestral"
    n = len([p for p in ref.rglob('*') if p.suffix.lower() in ('.wav', '.flac', '.mp3', '.ogg')]) if ref.exists() else 0
    print(f"  FAD reference recordings: {n} files in data/reference_orchestral"
          + ("" if n else " (get the frozen set with: python run_all.py fetch-reference)"))
    return 0


def cmd_voice(root: Path, args) -> int:
    from .voice import extract_melody, melody_to_midi, transcribe, transcript_to_lyrics
    if not (args.tune or args.words):
        print("Give --tune (a sung or hummed voice note) and/or --words (a spoken voice note).")
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.tune:
        m = extract_melody(args.tune)
        mid = melody_to_midi(m, out / "your_tune.mid", program=73)  # flute, easy to hear
        try:
            import soundfile as sf
            from .generators.midi import synthesize
            import pretty_midi
            sf.write(str(out / "your_tune.wav"), synthesize(pretty_midi.PrettyMIDI(str(mid)), 32000, m.duration + 0.5),
                     32000, subtype="PCM_16")
        except Exception as e:  # the MIDI file is the main result
            print(f"(could not render a preview WAV: {e})")
        names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        print(f"Tune: {len(m.notes)} notes, key {m.key_name}, {m.tempo} BPM")
        print("Notes: " + " ".join(f"{names[p % 12]}{p // 12 - 1}" for _, _, p in m.notes[:40]))
        for w in m.warnings:
            print(f"Note: {w}")
        print(f"Listen to what was heard: {out / 'your_tune.wav'} (MIDI: {mid})")
    if args.words:
        tr = transcribe(args.words, language=args.language)
        lyrics = transcript_to_lyrics(tr["text"])
        (out / "lyrics_from_voice.txt").write_text(lyrics, encoding="utf-8")
        print(f"Words ({tr['model']}):\n{lyrics}\nSaved to {out / 'lyrics_from_voice.txt'}; edit it, then use --lyrics.")
    return 0


def cmd_spec(request: str, duration: float) -> int:
    from .compiler import compile_prompt
    from .conductor import conduct, sections_to_dicts
    from .intent import parse_request
    from .orchestrator import orchestrate
    spec = parse_request("cli", request)
    orch = orchestrate(spec)
    sections = conduct(spec, duration)
    print(json.dumps({"spec": spec.to_dict(), "orchestration": orch.to_dict(),
                      "conductor_plan": sections_to_dicts(sections)}, indent=2))
    for cond in ("plain", "expert", "pipeline"):
        print(f"\n[{cond} prompt]\n{compile_prompt(cond, spec, orch, sections)}")
    return 0


def main(argv=None, root: Path | None = None) -> int:
    root = Path(root or Path.cwd())
    load_env(root / ".env")
    ap = argparse.ArgumentParser(prog="run_all.py", description=PROJECT_TITLE)
    ap.add_argument("--config", default=str(root / "config" / "study.yaml"))
    sub = ap.add_subparsers(dest="cmd")
    q = sub.add_parser("quick", help="few-minute smoke test (CPU is fine)")
    f = sub.add_parser("full", help="the preregistered study (GPU recommended)")
    for p in (q, f):
        p.add_argument("--generators", nargs="+")
        p.add_argument("--seeds", nargs="+", type=int)
        p.add_argument("--requests", nargs="+", help="request ids, e.g. r01 r02")
        p.add_argument("--duration", type=float)
        p.add_argument("--resume", help="run id to continue after an interruption")
        p.add_argument("--no-judge", action="store_true")
        p.add_argument("--allow-missing", action="store_true", help="skip unavailable parts instead of stopping")
        p.add_argument("--out", help="results folder (default: results/)")
        p.add_argument("--no-showcase", action="store_true", help="skip the KeyurTattva showcase songs after the run")
    s = sub.add_parser("song", help="make several refined versions of one song")
    s.add_argument("--request", required=True, help='e.g. "An epic Bollywood love song with strings and choir"')
    g = s.add_mutually_exclusive_group()
    g.add_argument("--lyrics", help="your lyric file, e.g. lyrics/my_song.txt")
    g.add_argument("--write-lyrics", action="store_true", help="let the open language model write lyrics")
    g.add_argument("--voice-lyrics", help="a voice note of you SPEAKING the lyrics (wav, mp3, m4a, ogg)")
    s.add_argument("--voice-tune", help="a voice note of you SINGING or HUMMING the tune; it becomes the theme")
    s.add_argument("--voice-language", help="language of the spoken lyrics for Whisper, e.g. english, hindi, gujarati")
    s.add_argument("--language", default="English")
    s.add_argument("--theme", help="what the lyrics should be about")
    s.add_argument("--versions", type=int, help="how many versions (default from config: 3)")
    s.add_argument("--generator", choices=["musicgen", "musicgen_melody", "stable_audio", "midi", "suno"])
    s.add_argument("--seed", type=int)
    s.add_argument("--duration", type=float)
    s.add_argument("--judge", dest="judge", action="store_true", default=None)
    s.add_argument("--no-judge", dest="judge", action="store_false")
    s.add_argument("--purpose", choices=["explore", "publish"], default="explore",
                   help="explore: try anything (not cleared for release); publish: Tattva mode, rights-safe routes only")
    s.add_argument("--out")
    vo = sub.add_parser("voice", help="check a voice note: hear the tune found, or see the lyrics typed out")
    vo.add_argument("--tune", help="a sung or hummed voice note")
    vo.add_argument("--words", help="a spoken voice note")
    vo.add_argument("--language", help="language of the spoken words, e.g. english, hindi")
    vo.add_argument("--out", default="voice_check", help="folder for the results (default: voice_check/)")
    sp = sub.add_parser("spec", help="show the specification, plans and prompts for a request")
    sp.add_argument("--request", required=True)
    sp.add_argument("--duration", type=float, default=30)
    v = sub.add_parser("verify", help="check every SHA-256 hash in a results or song folder")
    v.add_argument("folder")
    sub.add_parser("check", help="show which parts are installed and which keys are set")
    sh = sub.add_parser("showcase", help="make the KeyurTattva showcase songs (config/showcase.yaml)")
    sh.add_argument("--mode", choices=["quick", "full"], default="quick", help="which settings to use")
    sh.add_argument("--songs", nargs="+", help="song ids, e.g. h15 h13 (default: from the config)")
    sh.add_argument("--generator", help="override the generator, e.g. midi")
    sh.add_argument("--versions", type=int)
    sh.add_argument("--duration", type=float)
    fr = sub.add_parser("fetch-reference", help="download the frozen FAD reference recordings (about 3 GB)")
    fr.add_argument("--source", choices=["mtg-fast", "mtg"], default="mtg-fast")
    fr.add_argument("--keep-archives", action="store_true", help="keep the downloaded archives in data/cache")
    a = sub.add_parser("app", help="open the browser app (KeyurTattva Orchestra Studio)")
    a.add_argument("--share", action="store_true", help="public link, e.g. on Google Colab")
    a.add_argument("--port", type=int, default=7860)
    a.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args(argv)
    cmd = args.cmd or "quick"

    if cmd == "check":
        return cmd_check(root)
    if cmd == "app":
        try:
            from .app import launch
        except ImportError:
            print("The app needs Gradio: python3 -m pip install -r requirements.txt")
            return 1
        launch(root, share=args.share, port=args.port, host=args.host)
        return 0
    if cmd == "voice":
        return cmd_voice(root, args)
    if cmd == "showcase":
        from .showcase import run_showcase
        run_showcase(root, Path(args.config), args.mode, only=args.songs, generator=args.generator,
                     versions=args.versions, duration=args.duration)
        return 0
    if cmd == "fetch-reference":
        from .reference import ReferenceError, fetch_reference
        try:
            fetch_reference(root, source=args.source, keep_archives=args.keep_archives)
        except (ReferenceError, OSError) as e:
            print(f"Could not fetch the reference set: {e}")
            return 1
        return 0
    if cmd == "spec":
        return cmd_spec(args.request, args.duration)
    if cmd == "verify":
        from .provenance import verify_sums
        n, problems = verify_sums(Path(args.folder))
        if problems:
            print(f"FAILED: {len(problems)} problem(s) in {n} listed files")
            for p in problems:
                print("  " + p)
            return 1
        print(f"OK: all {n} files match their SHA-256 hashes")
        return 0
    if cmd == "song":
        from .publish import PublishBlocked
        from .song import run_song
        try:
            run_song(root, Path(args.config), args.request, args.lyrics, args.write_lyrics, args.language,
                     args.theme, args.versions, args.generator, args.seed, args.duration, args.judge,
                     Path(args.out) if args.out else None, purpose=args.purpose, voice_tune=args.voice_tune,
                     voice_lyrics=args.voice_lyrics, voice_language=args.voice_language)
        except PublishBlocked as e:
            print(f"Publish mode stopped before making anything:\n{e}")
            return 2
        return 0
    from .runner import run_study
    if args.cmd is None:  # bare "python run_all.py" = quick
        args = ap.parse_args(["quick"])
    overrides = {"generators": args.generators, "seeds": args.seeds, "request_ids": args.requests,
                 "duration_s": args.duration, "no_judge": args.no_judge, "allow_missing": args.allow_missing}
    run_study(root, Path(args.config), args.cmd, Path(args.out) if args.out else None, overrides, args.resume)
    if not args.no_showcase:
        from .showcase import run_showcase
        run_showcase(root, Path(args.config), args.cmd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
