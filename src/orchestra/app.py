# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Browser app (Gradio) for every feature of the pipeline.

Start it with ``python run_all.py app`` and open the address it prints. Everything runs on
your own computer (or your own Colab with ``--share``). The app calls exactly the same code
as the command line, so every run still writes its manifest, reports and SHA-256 hashes.

Tabs: Dashboard | Song studio | Plan preview | Lyrics workshop | Study runner | Results library |
Benchmark | Setup and keys | About and cite | Help.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from . import AUTHOR, PROJECT_TITLE, __version__

MAX_VERSIONS = 5
GENERATORS = ["midi", "musicgen", "stable_audio", "suno"]
SONG_GENERATORS = GENERATORS + ["musicgen_melody"]
GEN_LABELS = {"midi": "MIDI route (your own composer, CPU)", "musicgen": "MusicGen (open, GPU)",
              "musicgen_melody": "MusicGen-melody (follows your sung tune, GPU, explore only)",
              "stable_audio": "Stable Audio Open (open, GPU, HF token)", "suno": "Suno (paid, sings words)"}
ENV_KEYS = ["HF_TOKEN", "SOUNDFONT_PATH", "SUNO_API_BASE", "SUNO_API_KEY",
            "SUNO_PAID_PLAN", "STABLE_AUDIO_LICENCE_ACCEPTED"]
EXAMPLES = [
    "A romantic Bollywood song with lush strings, bansuri flute and choir that builds to a big final chorus",
    "An epic trailer cue for full orchestra, choir and hybrid percussion with braams, growing to a huge climax",
    "Raga Yaman evening piece with sitar, tabla and bansuri, slow alap building to a fast jhala",
    "A joyful Gujarati garba with dhol, harmonium, bansuri and strings",
    "A heroic overture for full symphony orchestra that starts quietly and ends with full brass and timpani",
    "A gentle lullaby for celesta, harp and solo violin with soft dynamics throughout",
]
CSS = """
:root, .dark {
  --kt-bg: #05060f; --kt-panel: rgba(18, 22, 44, .62); --kt-line: rgba(124, 92, 255, .28);
  --kt-cyan: #22e4ff; --kt-violet: #8b5cff; --kt-pink: #ff4fd8; --kt-amber: #ffb547; --kt-green: #2cffa0;
  --kt-text: #e9ecff; --kt-dim: #9aa3d6;
}
body, .gradio-container {background: var(--kt-bg) !important; color: var(--kt-text) !important;}
.gradio-container {
  max-width: min(1320px, 100vw) !important; width: 100% !important; box-sizing: border-box; margin: 0 auto !important;
  background:
    radial-gradient(900px 500px at 8% -10%, rgba(139,92,255,.28), transparent 60%),
    radial-gradient(700px 420px at 100% 0%, rgba(34,228,255,.18), transparent 60%),
    radial-gradient(800px 600px at 50% 120%, rgba(255,79,216,.12), transparent 60%),
    linear-gradient(rgba(124,92,255,.05) 1px, transparent 1px) 0 0 / 100% 32px,
    linear-gradient(90deg, rgba(124,92,255,.05) 1px, transparent 1px) 0 0 / 32px 100%,
    var(--kt-bg) !important;
}
.kt-header {position: relative; overflow: hidden; padding: 26px 30px 22px; border-radius: 20px; margin-bottom: 10px;
  background: linear-gradient(120deg, rgba(139,92,255,.35), rgba(34,228,255,.12) 55%, rgba(255,79,216,.25));
  border: 1px solid var(--kt-line); box-shadow: 0 0 40px rgba(139,92,255,.25), inset 0 0 30px rgba(34,228,255,.08);
  backdrop-filter: blur(14px);}
.kt-header .kt-title {margin: 4px 0 0; font-size: 2.3rem; line-height: 1.15; letter-spacing: .04em; font-weight: 700;
  color: #ffffff !important; text-shadow: 0 0 18px rgba(34,228,255,.75), 0 0 42px rgba(255,79,216,.45);}
.kt-title span {color: var(--kt-cyan) !important;}
.kt-header p {margin: 6px 0 0; color: var(--kt-dim);}
.kt-tag {font-family: 'JetBrains Mono', monospace; font-size: .75rem; letter-spacing: .25em; color: var(--kt-cyan);
  text-transform: uppercase;}
.kt-badge {display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: .78rem; margin: 10px 6px 0 0;
  border: 1px solid var(--kt-line); background: rgba(10,12,30,.55); color: var(--kt-text);}
.kt-eq {position: absolute; right: 28px; top: 22px; display: flex; gap: 5px; align-items: flex-end; height: 64px;}
.kt-eq span {width: 7px; border-radius: 4px; background: linear-gradient(var(--kt-pink), var(--kt-cyan));
  box-shadow: 0 0 12px rgba(34,228,255,.6); animation: kt-eq 1.2s ease-in-out infinite;}
.kt-eq span:nth-child(2){animation-delay:.15s}.kt-eq span:nth-child(3){animation-delay:.3s}
.kt-eq span:nth-child(4){animation-delay:.45s}.kt-eq span:nth-child(5){animation-delay:.6s}
.kt-eq span:nth-child(6){animation-delay:.75s}.kt-eq span:nth-child(7){animation-delay:.9s}
@keyframes kt-eq {0%,100%{height:14px} 50%{height:62px}}
html, body {overflow-x: hidden;}
@media (max-width: 700px) {.kt-eq {display: none} .kt-header {padding: 16px;} .kt-header .kt-title {font-size: 1.45rem}
  .kt-header p {font-size: .85rem} .kt-badge {font-size: .7rem; margin-top: 6px}
  .gradio-container {padding-left: 8px !important; padding-right: 8px !important; min-width: 0 !important; width: 100% !important;}
  .kt-cards {grid-template-columns: 1fr 1fr;}}
.kt-cards {display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px;}
.kt-card {padding: 14px 16px; border-radius: 16px; background: var(--kt-panel); border: 1px solid var(--kt-line);
  box-shadow: inset 0 0 24px rgba(139,92,255,.08);}
.kt-card .k {font-size: .72rem; letter-spacing: .18em; text-transform: uppercase; color: var(--kt-dim);}
.kt-card .v {font-size: 1.5rem; font-weight: 700; margin-top: 4px; color: var(--kt-text);}
.kt-card .v.on {color: var(--kt-green); text-shadow: 0 0 12px rgba(44,255,160,.5);}
.kt-card .v.off {color: var(--kt-amber);}
.kt-explore, .kt-publish, .kt-block {padding: 10px 14px; border-radius: 12px; backdrop-filter: blur(8px); color: var(--kt-text);}
.kt-explore {border: 1px solid rgba(255,181,71,.5); background: rgba(255,181,71,.08); box-shadow: 0 0 18px rgba(255,181,71,.15);}
.kt-publish {border: 1px solid rgba(44,255,160,.5); background: rgba(44,255,160,.08); box-shadow: 0 0 18px rgba(44,255,160,.18);}
.kt-block {border: 1px solid rgba(255,79,100,.6); background: rgba(255,79,100,.10); box-shadow: 0 0 18px rgba(255,79,100,.2);}
.block, .form, .panel, .gr-group {background: var(--kt-panel) !important; border-color: var(--kt-line) !important;
  border-radius: 16px !important; backdrop-filter: blur(10px);}
button.primary, .primary {background: linear-gradient(90deg, var(--kt-violet), var(--kt-cyan)) !important; color: #05060f !important;
  font-weight: 700 !important; border: none !important; box-shadow: 0 0 22px rgba(34,228,255,.35) !important;
  transition: transform .15s ease, box-shadow .15s ease;}
button.primary:hover {transform: translateY(-1px); box-shadow: 0 0 34px rgba(139,92,255,.6) !important;}
.tab-nav button, [role="tab"] {font-weight: 600 !important; letter-spacing: .03em;}
[role="tab"][aria-selected="true"] {color: var(--kt-cyan) !important; border-color: var(--kt-cyan) !important;
  text-shadow: 0 0 10px rgba(34,228,255,.6);}
textarea, input {font-family: 'Space Grotesk', system-ui, sans-serif;}
.kt-log textarea {font-family: 'JetBrains Mono', monospace !important; font-size: .82rem !important; color: var(--kt-green) !important;
  background: rgba(2,4,12,.85) !important;}
footer {visibility: hidden;}
"""


# ---------------------------------------------------------------- helpers
class Job:
    """Runs one long task at a time in a thread and collects its log lines for streaming."""
    lock = threading.Lock()

    def __init__(self):
        self.lines: list[str] = []
        self.result = None
        self.error: str | None = None
        self.done = False

    def log(self, msg):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.lines.append(f"[{stamp}] {msg}")

    def start(self, fn, *args, **kwargs):
        def run():
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    self.result = fn(*args, log=self.log, **kwargs)
                for line in buf.getvalue().splitlines():
                    if line.strip():
                        self.log(line)
            except Exception as e:  # shown to the user in the log
                self.error = f"{type(e).__name__}: {e}"
                self.log("ERROR " + self.error)
            finally:
                self.done = True
        threading.Thread(target=run, daemon=True).start()

    def text(self) -> str:
        return "\n".join(self.lines[-400:])


def _cfg(root: Path) -> dict:
    return yaml.safe_load((root / "config" / "study.yaml").read_text(encoding="utf-8"))


def _requests(root: Path) -> list[dict]:
    return yaml.safe_load((root / "config" / "requests.yaml").read_text(encoding="utf-8"))["requests"]


def _zip(folder: Path) -> str:
    out = Path(shutil.make_archive(str(folder), "zip", root_dir=folder.parent, base_dir=folder.name))
    return str(out)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "song"


def _folders(root: Path) -> list[str]:
    items = []
    for base in ("songs", "results"):
        d = root / base
        if d.exists():
            for p in d.rglob("manifest.json"):
                items.append(p.parent)
    items.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p.relative_to(root)) for p in items]


def purpose_banner(purpose: str, generator: str) -> str:
    from .publish import POLICY
    if purpose.startswith("Explore"):
        return ("<div class='kt-explore'><b>Explore mode.</b> Any model is allowed. Every file is marked "
                "<i>\"Exploration output - not cleared for release\"</i>. Use it to try ideas, not to release.</div>")
    rule = POLICY.get(generator, {})
    if not rule.get("allowed"):
        return f"<div class='kt-block'><b>Blocked in Tattva publish mode.</b> {rule.get('reason', '')}</div>"
    need = rule.get("declarations") or []
    missing = [d for d in need if os.environ.get(d, "").strip().lower() not in ("yes", "true", "1")]
    extra = (f"<br><b>Needs your declaration:</b> {', '.join(missing)}=yes (set it in <i>Setup and keys</i>)."
             if missing else "")
    return (f"<div class='kt-publish'><b>Tattva publish mode.</b> {rule['basis']} You also get a release "
            f"checklist, an AI disclosure text and a human-contribution log.{extra}</div>")


def guide_markdown(root: Path) -> str:
    """docs/APP_GUIDE.md with its screenshots served by the app."""
    import gradio as gr
    src = root / "docs" / "APP_GUIDE.md"
    if not src.exists():
        return "The guide is missing: see docs/APP_GUIDE.md in the package."
    prefix = "/gradio_api/file=" if int(gr.__version__.split(".")[0]) >= 5 else "/file="
    text = src.read_text(encoding="utf-8")
    return re.sub(r"!\[([^\]]*)\]\((screenshots/[^)]+)\)",
                  lambda m: f"![{m.group(1)}]({prefix}{(src.parent / m.group(2)).resolve().as_posix()})", text)


def _has(mod: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(mod) is not None


def dashboard_html(root: Path) -> str:
    folders = _folders(root)
    songs = sum(f.startswith("songs") for f in folders)
    runs = len(folders) - songs
    gpu = "none"
    if _has("torch"):
        try:
            import torch
            gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU only"
        except Exception:
            gpu = "unknown"
    def card(k, v, on=None):
        cls = "" if on is None else (" on" if on else " off")
        return f"<div class='kt-card'><div class='k'>{k}</div><div class='v{cls}'>{v}</div></div>"
    sf = os.environ.get("SOUNDFONT_PATH")
    cards = [card("Songs made", songs), card("Study runs", runs),
             card("AI models", "ready" if _has("torch") and _has("transformers") else "not installed",
                  _has("torch") and _has("transformers")),
             card("GPU", gpu if len(gpu) < 18 else gpu[:16] + "…", gpu not in ("none", "CPU only", "unknown")),
             card("Pro MIDI sound", "soundfont set" if sf and Path(sf).exists() else "demo synth",
                  bool(sf and Path(sf).exists())),
             card("Stable Audio key", "set" if os.environ.get("HF_TOKEN") else "not set", bool(os.environ.get("HF_TOKEN"))),
             card("Suno", "connected" if os.environ.get("SUNO_API_KEY") else "off", bool(os.environ.get("SUNO_API_KEY"))),
             card("Artist", "KeyurTattva")]
    return "<div class='kt-cards'>" + "".join(cards) + "</div>"


def recent_table(root: Path) -> pd.DataFrame:
    rows = []
    for f in _folders(root)[:15]:
        try:
            m = json.loads((root / f / "manifest.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        rows.append({"when (UTC)": (m.get("started_utc") or "")[:16].replace("T", " "),
                     "type": m.get("kind", ""), "purpose": m.get("purpose") or "explore",
                     "request or mode": (m.get("request") or m.get("mode") or "")[:70],
                     "best": f"v{m['best_version']}" if m.get("best_version") else "", "folder": f})
    return pd.DataFrame(rows, columns=["when (UTC)", "type", "purpose", "request or mode", "best", "folder"])


# ---------------------------------------------------------------- plan preview
def preview(request: str, duration: float, generator: str):
    from .compiler import compile_prompt
    from .conductor import conduct, dynamics_curve, sections_to_dicts
    from .intent import parse_request
    from .orchestrator import orchestrate
    if not request.strip():
        raise ValueError("Type a request first.")
    root_cfg = None
    spec = parse_request("app", request)
    orch = orchestrate(spec)
    sections = conduct(spec, duration)
    s = spec.to_dict()
    summary = (f"**Ensemble:** {s['ensemble']} &nbsp; **Families:** {', '.join(s['families'])}  \n"
               f"**Mood:** {s['mood']} &nbsp; **Scale:** {s['scale']} &nbsp; **Tempo:** {s['tempo']} BPM "
               f"in {s['metre']} &nbsp; **Form:** {s['form']} &nbsp; **Dynamic shape:** {s['dynamics_shape']}"
               + (f"  \n**Culture:** {s['culture']}" if s.get("culture") else "")
               + ("".join(f"  \n- note: {n}" for n in s.get("notes") or []))
               + ("".join(f"  \n- warning: {w}" for w in orch.to_dict().get("warnings") or [])))
    parts = pd.DataFrame(orch.to_dict()["parts"])
    secs = pd.DataFrame(sections_to_dicts(sections))
    if "active_families" in secs:
        secs["active_families"] = secs["active_families"].apply(lambda v: ", ".join(v) if isinstance(v, list) else v)
    curve = dynamics_curve(sections, duration, hop=0.5)
    plot = pd.DataFrame({"time (s)": [0.25 + 0.5 * i for i in range(len(curve))], "planned level (dB)": curve})
    words = {"musicgen": 90, "stable_audio": 60, "suno": 120, "midi": 90}.get(generator, 90)
    prompts = {c: compile_prompt(c, spec, orch, sections, max_words=words) for c in ("plain", "expert", "pipeline")}
    full = json.dumps({"spec": s, "orchestration": orch.to_dict(), "conductor_plan": sections_to_dicts(sections)},
                      indent=2, default=str)
    return summary, parts, secs, plot, prompts["plain"], prompts["expert"], prompts["pipeline"], full


# ---------------------------------------------------------------- lyrics
def lyric_check(text: str, request: str):
    from .intent import parse_request
    from .lyrics import count_syllables, lyric_fit, parse_lyrics, target_syllables
    if not text.strip():
        return "Paste or write lyrics first.", pd.DataFrame()
    spec = parse_request("app", request or "a song")
    secs = parse_lyrics(text)
    fit = lyric_fit(secs, spec.tempo, spec.metre)
    lo, hi = fit["syllable_range"]
    rows = [{"section": s.tag, "line": l, "syllables": count_syllables(l),
             "fits": "yes" if lo <= count_syllables(l) <= hi else ("too long" if count_syllables(l) > hi else "short")}
            for s in secs for l in s.lines]
    msg = (f"**{fit['lines_in_range']} of {fit['lines']} lines fit** ({fit['fit']:.0%}) at {spec.tempo} BPM in "
           f"{spec.metre}: aim for {lo} to {hi} syllables per line. Sections found: "
           f"{', '.join(dict.fromkeys(s.tag for s in secs)) or 'none (add [verse], [chorus] tags)'}.")
    return msg, pd.DataFrame(rows)


def save_lyrics(root: Path, text: str, name: str):
    if not text.strip():
        raise ValueError("Nothing to save.")
    d = root / "lyrics"
    d.mkdir(exist_ok=True)
    p = d / f"{_slug(name or 'my_song')}.txt"
    p.write_text(text.strip() + "\n", encoding="utf-8")
    return f"Saved to `{p.relative_to(root)}`.", str(p)


def write_lyrics_ai(root: Path, request: str, language: str, theme: str, seed: int):
    from .intent import parse_request
    from .lyrics import LyricsWriter
    lw = _cfg(root)["song"]["lyrics_writer"]
    spec = parse_request("app", request or "a song")
    w = LyricsWriter(lw["model_id"], lw.get("temperature", 0.8), lw.get("max_new_tokens", 500))
    return w.write(request, spec.mood, spec.tempo, spec.metre, "song", language, theme or None, int(seed))


# ---------------------------------------------------------------- build the app
def build(root: Path):
    import gradio as gr
    root = Path(root)
    cfg = _cfg(root)
    reqs = _requests(root)
    req_choices = [f"{r['id']}: {r['text']}" for r in reqs]

    with gr.Blocks(title=f"KeyurTattva Orchestra Studio") as demo:
        gr.HTML(f"""<div class='kt-header'><div class='kt-eq'><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
<div class='kt-tag'>AI orchestra engine · v{__version__}</div><div class='kt-title'>KeyurTattva <span>Orchestra Studio</span></div>
<p>{PROJECT_TITLE}: describe a piece, plan it like a score, generate, measure and improve it.</p>
<p><span class='kt-badge'>Full orchestra + choir + Indian instruments</span><span class='kt-badge'>Explore or Tattva publish</span>
<span class='kt-badge'>SHA-256 hashed</span><span class='kt-badge'>Open source</span></p></div>""")

        # ------------------------------------------------ Dashboard
        with gr.Tab("Dashboard"):
            d_cards = gr.HTML(dashboard_html(root))
            d_ref = gr.Button("Refresh status")
            d_recent = gr.Dataframe(recent_table(root), label="Recent songs and runs", interactive=False)
            gr.Markdown("**New here?** Open the **Help** tab for a step-by-step guide.  \n**Start here:** plan a piece in *Plan preview*, make it in *Song studio*, check the words in "
                        "*Lyrics workshop*, run the research in *Study runner*, and open anything later in *Results library*.")
            d_ref.click(lambda: (dashboard_html(root), recent_table(root)), None, [d_cards, d_recent])

        # ------------------------------------------------ Song studio
        with gr.Tab("Song studio"):
            with gr.Row():
                with gr.Column(scale=3):
                    s_req = gr.Textbox(label="Describe your piece", lines=3, value=EXAMPLES[0],
                                       placeholder="Instruments, mood, culture, how it should grow...")
                    s_ex = gr.Dropdown(EXAMPLES, label="Or start from an example", value=None)
                    with gr.Row():
                        s_purpose = gr.Radio(["Explore", "Tattva publish"], value="Explore", label="Purpose")
                        s_gen = gr.Dropdown([(GEN_LABELS[g], g) for g in SONG_GENERATORS], value="midi", label="Generator")
                    s_banner = gr.HTML(purpose_banner("Explore", "midi"))
                    s_lsrc = gr.Radio(["No lyrics (instrumental)", "My lyrics", "From my voice note (spoken)",
                                       "Write lyrics with AI (Qwen2.5)"],
                                      value="No lyrics (instrumental)", label="Lyrics")
                    with gr.Group(visible=False) as s_mine:
                        s_lyr = gr.Textbox(label="Your lyrics (use [verse], [chorus] tags)", lines=8,
                                           value=_read(root / "lyrics" / "example_song.txt"))
                        s_lfile = gr.File(label="...or upload a .txt lyric file", file_types=[".txt"])
                    with gr.Row(visible=False) as s_ai:
                        s_lang = gr.Textbox(label="Language", value="English")
                        s_theme = gr.Textbox(label="Theme", placeholder="first monsoon rain")
                    with gr.Accordion("Voice notes: sing your tune or speak your lyrics", open=False):
                        gr.Markdown("Record with your microphone or upload a voice note (wav, mp3, m4a, ogg). "
                                    "Everything stays on your computer. **Your tune** becomes the main theme: the "
                                    "MIDI route plays and harmonises it, MusicGen-melody follows it. **Your words** "
                                    "are typed out by Whisper and become the lyrics.")
                        with gr.Row():
                            with gr.Column():
                                s_vtune = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                                   label="Sing or hum your tune")
                                s_vcheck = gr.Button("Hear the tune I found")
                                s_vinfo = gr.Markdown()
                                s_vprev = gr.Audio(label="Your tune as notes (flute)", type="filepath",
                                                   interactive=False, visible=False)
                            with gr.Column():
                                s_vwords = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                                    label="Speak your lyrics")
                                s_vlang = gr.Textbox(label="Language of the words", placeholder="english, hindi, gujarati (blank = detect)")
                                s_vtrans = gr.Button("Type out my words")
                                s_vmsg = gr.Markdown()
                with gr.Column(scale=2):
                    s_versions = gr.Slider(1, MAX_VERSIONS, value=3, step=1, label="Versions (each improves on the last)")
                    s_dur = gr.Slider(6, 120, value=30, step=1, label="Length (seconds)")
                    s_seed = gr.Number(value=11, precision=0, label="Seed (same seed = same result)")
                    s_judge = gr.Checkbox(value=False, label="Use the AI judge (Qwen2-Audio, needs a big GPU)")
                    s_go = gr.Button("Make song", variant="primary", size="lg")
                    s_log = gr.Textbox(label="Live log", lines=12, max_lines=12, autoscroll=True, elem_classes="kt-log")
            s_best = gr.Markdown()
            with gr.Row():
                s_audio = [gr.Audio(label=f"v{i + 1}", visible=False, type="filepath", interactive=False)
                           for i in range(MAX_VERSIONS)]
            s_table = gr.Dataframe(label="Scores per version (higher is better)", interactive=False)
            with gr.Accordion("Song report", open=False):
                s_report = gr.Markdown()
            with gr.Accordion("Release pack (Tattva publish)", open=False):
                s_release = gr.Markdown()
                s_human = gr.Textbox(label="HUMAN_CONTRIBUTIONS.md: write what you did by hand", lines=8)
                s_save_human = gr.Button("Save my contributions")
                s_human_msg = gr.Markdown()
            s_folder = gr.State("")
            s_files = gr.File(label="Download", file_count="multiple")

            s_ex.change(lambda e: e or gr.skip(), s_ex, s_req)
            s_purpose.change(purpose_banner, [s_purpose, s_gen], s_banner)
            s_gen.change(purpose_banner, [s_purpose, s_gen], s_banner)
            s_lsrc.change(lambda v: (gr.Group(visible=v == "My lyrics"), gr.Row(visible=v.startswith("Write"))),
                          s_lsrc, [s_mine, s_ai])

            def check_tune(path):
                if not path:
                    return "Record or upload a voice note first.", gr.Audio(visible=False, value=None)
                from .voice import extract_melody, melody_to_midi
                try:
                    m = extract_melody(path)
                except Exception as e:
                    return f"**No tune found.** {e}", gr.Audio(visible=False, value=None)
                tmp = root / "songs" / "_voice_preview"
                tmp.mkdir(parents=True, exist_ok=True)
                mid = melody_to_midi(m, tmp / "your_tune.mid", program=73)
                import pretty_midi
                import soundfile as sf
                from .generators.midi import synthesize
                wav = tmp / "your_tune.wav"
                sf.write(str(wav), synthesize(pretty_midi.PrettyMIDI(str(mid)), 32000, m.duration + 0.5), 32000,
                         subtype="PCM_16")
                names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
                notes = " ".join(f"{names[p % 12]}{p // 12 - 1}" for _, _, p in m.notes[:24])
                warn = "".join(f"\n\n> {w}" for w in m.warnings)
                return (f"**{len(m.notes)} notes**, key **{m.key_name}**, **{m.tempo} BPM**  \n`{notes}`{warn}",
                        gr.Audio(value=str(wav), visible=True))
            s_vcheck.click(check_tune, s_vtune, [s_vinfo, s_vprev])

            def type_words(path, lang):
                if not path:
                    return gr.skip(), gr.skip(), "Record or upload a spoken voice note first."
                from .voice import transcribe, transcript_to_lyrics
                try:
                    tr = transcribe(path, language=(lang or "").strip().lower() or None)
                except Exception as e:
                    return gr.skip(), gr.skip(), f"**Could not transcribe.** {e}"
                return (transcript_to_lyrics(tr["text"]), "My lyrics",
                        f"Typed out by {tr['model']}. Check and edit the lyrics in the box above, then make the song.")
            s_vtrans.click(type_words, [s_vwords, s_vlang], [s_lyr, s_lsrc, s_vmsg])
            s_lfile.upload(lambda f: Path(f).read_text(encoding="utf-8", errors="replace") if f else "", s_lfile, s_lyr)

            def make_song(req, purpose, gen, lsrc, lyr, lang, theme, versions, dur, seed, judge, vtune, vwords, vlang):
                from .song import run_song
                if not req.strip():
                    raise gr.Error("Describe your piece first.")
                if not Job.lock.acquire(blocking=False):
                    raise gr.Error("Another job is running. Wait for it to finish.")
                hidden = [gr.Audio(visible=False, value=None) for _ in range(MAX_VERSIONS)]
                try:
                    lyrics_path = None
                    if lsrc == "My lyrics" and lyr.strip():
                        lyrics_path = root / "lyrics" / f"app_{datetime.now():%Y%m%d-%H%M%S}.txt"
                        lyrics_path.parent.mkdir(exist_ok=True)
                        lyrics_path.write_text(lyr.strip() + "\n", encoding="utf-8")
                    job = Job()
                    job.start(run_song, root, root / "config" / "study.yaml", req,
                              lyrics_path=str(lyrics_path) if lyrics_path else None,
                              write_lyrics=lsrc.startswith("Write"), language=lang or "English",
                              theme=theme or None, versions=int(versions), generator=gen, seed=int(seed),
                              duration=float(dur), judge=bool(judge), out_dir=None,
                              purpose="publish" if purpose.startswith("Tattva") else "explore",
                              voice_tune=vtune or None,
                              voice_lyrics=vwords if (lsrc.startswith("From my voice") and vwords) else None,
                              voice_language=(vlang or "").strip().lower() or None)
                    while not job.done:
                        yield (job.text(), "", *hidden, None, "", "", "", "", None)
                        time.sleep(0.5)
                    if job.error:
                        yield (job.text(), f"### Stopped\n{job.error}", *hidden, None, "", "", "", "", None)
                        return
                    folder = Path(job.result)
                    df = pd.read_csv(folder / "versions.csv")
                    best = _read(folder / "BEST.txt").strip()
                    audios = []
                    for i in range(MAX_VERSIONS):
                        wav = folder / f"v{i + 1}.wav"
                        if wav.exists():
                            sc = df.loc[df["version"] == i + 1, "score"]
                            star = " (best)" if wav.name == best else ""
                            audios.append(gr.Audio(value=str(wav), visible=True,
                                                   label=f"v{i + 1}{star}: score {float(sc.iloc[0]):.3f}"))
                        else:
                            audios.append(gr.Audio(visible=False, value=None))
                    cols = [c for c in ["version", "score", "prompt_adherence", "section_clarity_raw",
                                        "dynamics_accuracy", "structure_f", "judge_overall", "tune_similarity",
                                        "changes", "outcome", "seed"] if c in df]
                    files = [str(p) for p in [folder / best, folder / best.replace(".wav", ".mid"),
                                              folder / "song_report.pdf", folder / "RELEASE_CHECKLIST.md",
                                              folder / "AI_DISCLOSURE.txt", folder / "OUTPUT_LICENSE.md"]
                             if p.exists()] + [_zip(folder)]
                    head = (f"### Done: best version is **{best}**\nFolder: `{folder.relative_to(root)}`. "
                            f"Every file is hashed in SHA256SUMS and credited to KeyurTattva.")
                    yield (job.text(), head, *audios, df[cols].round(3), _read(folder / "song_report.md"),
                           _read(folder / "RELEASE_CHECKLIST.md") or "_Explore mode: no release pack. "
                           "Remake the song in Tattva publish mode before release._",
                           _read(folder / "HUMAN_CONTRIBUTIONS.md"), str(folder), files)
                finally:
                    Job.lock.release()

            s_go.click(make_song, [s_req, s_purpose, s_gen, s_lsrc, s_lyr, s_lang, s_theme, s_versions,
                                   s_dur, s_seed, s_judge, s_vtune, s_vwords, s_vlang],
                       [s_log, s_best, *s_audio, s_table, s_report, s_release, s_human, s_folder, s_files])

            def save_human(folder, text):
                if not folder or not (Path(folder) / "HUMAN_CONTRIBUTIONS.md").exists():
                    return "Make a song in Tattva publish mode first."
                (Path(folder) / "HUMAN_CONTRIBUTIONS.md").write_text(text, encoding="utf-8")
                return "Saved. (This file is yours to edit, so it is not part of the SHA-256 check.)"
            s_save_human.click(save_human, [s_folder, s_human], s_human_msg)

        # ------------------------------------------------ Plan preview
        with gr.Tab("Plan preview"):
            gr.Markdown("See exactly how the pipeline reads your request and plans the music, before generating anything.")
            with gr.Row():
                p_req = gr.Textbox(label="Request", value=EXAMPLES[1], lines=2, scale=4)
                p_dur = gr.Slider(6, 120, value=30, step=1, label="Length (s)", scale=1)
                p_gen = gr.Dropdown([(GEN_LABELS[g], g) for g in GENERATORS], value="musicgen",
                                    label="Prompt word budget for", scale=1)
            p_go = gr.Button("Plan it", variant="primary")
            p_sum = gr.Markdown()
            with gr.Row():
                p_parts = gr.Dataframe(label="Orchestration: role, register (MIDI notes) and balance per instrument")
            p_secs = gr.Dataframe(label="Conductor plan: sections, dynamics, lead family, articulation")
            p_plot = gr.LinePlot(x="time (s)", y="planned level (dB)", label="Planned dynamics", height=260)
            with gr.Row():
                p_plain = gr.Textbox(label="Plain prompt", lines=5)
                p_expert = gr.Textbox(label="Expert prompt", lines=5)
                p_pipe = gr.Textbox(label="Pipeline prompt", lines=5)
            with gr.Accordion("Full plan (JSON)", open=False):
                p_json = gr.Code(language="json")

            def do_preview(r, d, g):
                try:
                    return preview(r, d, g)
                except ValueError as e:
                    raise gr.Error(str(e))
            p_go.click(do_preview, [p_req, p_dur, p_gen],
                       [p_sum, p_parts, p_secs, p_plot, p_plain, p_expert, p_pipe, p_json])

        # ------------------------------------------------ Lyrics workshop
        with gr.Tab("Lyrics workshop"):
            gr.Markdown("Write or paste lyrics, check that each line fits the tempo, and save them to `lyrics/`. "
                        "Only Suno sings words; with open models the lyrics are kept with the song.")
            with gr.Row():
                with gr.Column(scale=3):
                    l_text = gr.Textbox(label="Lyrics", lines=16, value=_read(root / "lyrics" / "example_song.txt"))
                    l_file = gr.File(label="Open a .txt file", file_types=[".txt"])
                with gr.Column(scale=2):
                    l_req = gr.Textbox(label="The song request (sets tempo and metre)", value=EXAMPLES[0], lines=2)
                    l_check = gr.Button("Check fit", variant="primary")
                    l_name = gr.Textbox(label="File name", value="my_song")
                    l_save = gr.Button("Save to lyrics/")
                    with gr.Accordion("Write with AI (free open model, GPU)", open=False):
                        l_lang = gr.Textbox(label="Language", value="English")
                        l_theme = gr.Textbox(label="Theme")
                        l_seed = gr.Number(value=11, precision=0, label="Seed")
                        l_write = gr.Button("Write lyrics")
                        gr.Markdown("_AI-written lyrics have weak copyright on their own: rewrite them in your words before release._")
            l_msg = gr.Markdown()
            l_table = gr.Dataframe(label="Line by line")
            l_dl = gr.File(label="Saved file")
            l_file.upload(lambda f: Path(f).read_text(encoding="utf-8", errors="replace") if f else "", l_file, l_text)
            l_check.click(lyric_check, [l_text, l_req], [l_msg, l_table])
            l_save.click(lambda t, n: save_lyrics(root, t, n), [l_text, l_name], [l_msg, l_dl])

            def do_write(r, lang, theme, seed):
                try:
                    return write_lyrics_ai(root, r, lang, theme, seed)
                except Exception as e:
                    raise gr.Error(f"Lyrics model unavailable: {e}. Install requirements-models.txt and use a GPU.")
            l_write.click(do_write, [l_req, l_lang, l_theme, l_seed], l_text)

        # ------------------------------------------------ Study runner
        with gr.Tab("Study runner"):
            gr.Markdown("Run the smoke test or the preregistered study. Quick mode checks the software; "
                        "**its numbers are not study results.**")
            with gr.Row():
                r_mode = gr.Radio(["quick", "full"], value="quick", label="Mode")
                r_gens = gr.CheckboxGroup(GENERATORS, value=["midi"], label="Generators (quick mode default: midi)")
            with gr.Row():
                r_seeds = gr.Textbox(value="", label="Seeds (blank = config)", placeholder="11 22 33")
                r_dur = gr.Number(value=0, precision=0, label="Length in seconds (0 = config)")
                r_judge = gr.Checkbox(value=True, label="No AI judge")
                r_allow = gr.Checkbox(value=False, label="Skip unavailable parts (--allow-missing)")
            r_reqs = gr.Dropdown(req_choices, multiselect=True, label="Requests (blank = config)")
            r_resume = gr.Dropdown([""] + [p.name for p in (root / "results").glob("*") if (p / "manifest.json").exists()],
                                   value="", label="Resume an interrupted run (optional)")
            r_go = gr.Button("Run", variant="primary")
            r_log = gr.Textbox(label="Live log", lines=14, max_lines=14, autoscroll=True, elem_classes="kt-log")
            r_head = gr.Markdown()
            r_tests = gr.Dataframe(label="Hypothesis tests")
            r_summary = gr.Dataframe(label="Summary by generator and condition")
            with gr.Accordion("Full report", open=False):
                r_report = gr.Markdown()
            r_files = gr.File(label="Download", file_count="multiple")

            def run_study_ui(mode, gens, seeds, dur, nojudge, allow, reqs_sel, resume):
                from .runner import run_study
                if not Job.lock.acquire(blocking=False):
                    raise gr.Error("Another job is running. Wait for it to finish.")
                try:
                    over = {"generators": gens or None,
                            "seeds": [int(s) for s in re.findall(r"\d+", seeds or "")] or None,
                            "request_ids": [r.split(":")[0] for r in reqs_sel] or None,
                            "duration_s": float(dur) if dur else None, "no_judge": bool(nojudge),
                            "allow_missing": bool(allow)}
                    job = Job()
                    job.start(run_study, root, root / "config" / "study.yaml", mode, None, over, resume or None)
                    while not job.done:
                        yield job.text(), "", None, None, "", None
                        time.sleep(0.7)
                    if job.error:
                        yield job.text(), f"### Stopped\n{job.error}", None, None, "", None
                        return
                    run = Path(job.result)
                    t = run / "tables"
                    tests = pd.read_csv(t / "hypothesis_tests.csv").round(4) if (t / "hypothesis_tests.csv").exists() else None
                    summ = pd.read_csv(t / "summary.csv").round(3) if (t / "summary.csv").exists() else None
                    files = [str(p) for p in [run / "report.pdf", run / "report.html"] if p.exists()] + [_zip(run)]
                    yield (job.text(), f"### Done: `{run.relative_to(root)}`", tests, summ,
                           _read(run / "report.md"), files)
                finally:
                    Job.lock.release()
            r_go.click(run_study_ui, [r_mode, r_gens, r_seeds, r_dur, r_judge, r_allow, r_reqs, r_resume],
                       [r_log, r_head, r_tests, r_summary, r_report, r_files])

        # ------------------------------------------------ Results library
        with gr.Tab("Results library"):
            with gr.Row():
                lib_sel = gr.Dropdown(_folders(root), label="Songs and study runs (newest first)", scale=4)
                lib_ref = gr.Button("Refresh", scale=1)
            with gr.Row():
                lib_verify = gr.Button("Verify SHA-256 hashes", variant="primary")
                lib_zip = gr.Button("Download as zip")
            lib_msg = gr.Markdown()
            lib_audio_sel = gr.Dropdown(label="Play a file")
            lib_audio = gr.Audio(type="filepath", interactive=False)
            with gr.Accordion("Report", open=True):
                lib_report = gr.Markdown()
            with gr.Accordion("Manifest (author, environment, hashes, timings)", open=False):
                lib_manifest = gr.Code(language="json")
            lib_files = gr.File(label="Download", file_count="multiple")

            lib_ref.click(lambda: gr.Dropdown(choices=_folders(root)), None, lib_sel)

            def open_folder(sel):
                if not sel:
                    return "", gr.Dropdown(choices=[]), "", ""
                f = root / sel
                wavs = sorted(str(p.relative_to(f)) for p in f.rglob("*.wav"))
                rep = _read(f / "song_report.md") or _read(f / "report.md")
                purpose = ""
                try:
                    m = json.loads(_read(f / "manifest.json"))
                    purpose = m.get("purpose") or "explore (study run)"
                except Exception:
                    m = {}
                return (f"**Folder:** `{sel}` &nbsp; **Purpose:** {purpose} &nbsp; **Files:** "
                        f"{sum(1 for p in f.rglob('*') if p.is_file())}", gr.Dropdown(choices=wavs, value=wavs[0] if wavs else None),
                        rep, json.dumps(m, indent=2)[:200000])
            lib_sel.change(open_folder, lib_sel, [lib_msg, lib_audio_sel, lib_report, lib_manifest])
            lib_audio_sel.change(lambda sel, a: str(root / sel / a) if sel and a else None, [lib_sel, lib_audio_sel], lib_audio)

            def verify(sel):
                from .provenance import verify_sums
                if not sel:
                    return "Pick a folder first."
                n, problems = verify_sums(root / sel)
                return (f"**OK:** all {n} files match their SHA-256 hashes." if not problems else
                        f"**FAILED:** {len(problems)} problem(s):\n" + "\n".join(f"- {p}" for p in problems[:50]))
            lib_verify.click(verify, lib_sel, lib_msg)
            lib_zip.click(lambda sel: [_zip(root / sel)] if sel else None, lib_sel, lib_files)

        # ------------------------------------------------ Benchmark
        with gr.Tab("Benchmark"):
            gr.Markdown(f"The {len(reqs)} preregistered requests and their author-written targets. "
                        "They are fixed before data collection; edit `config/requests.yaml` only before registering.")
            bench = pd.DataFrame([{"id": r["id"], "request": r["text"],
                                   "families": ", ".join(r["targets"]["families"]), "form": r["targets"]["form"],
                                   "shape": r["targets"]["shape"], "culture": r["targets"].get("culture", "")}
                                  for r in reqs])
            b_filter = gr.Textbox(label="Filter", placeholder="raga, brass, choir...")
            b_table = gr.Dataframe(bench, interactive=False, wrap=True)
            b_filter.change(lambda q: bench[bench.apply(lambda row: q.lower() in " ".join(map(str, row)).lower(), axis=1)]
                            if q else bench, b_filter, b_table)

        # ------------------------------------------------ Setup and keys
        with gr.Tab("Setup and keys"):
            k_check = gr.Button("Check my setup", variant="primary")
            k_out = gr.Code(label="What is installed", language=None)
            gr.Markdown("### Keys and declarations\nSaved to `.env` on this computer only. Never share that file.")
            env_now = {k: os.environ.get(k, "") for k in ENV_KEYS}
            k_hf = gr.Textbox(label="HF_TOKEN (Stable Audio Open)", type="password", value=env_now["HF_TOKEN"])
            k_sf = gr.Textbox(label="SOUNDFONT_PATH (realistic MIDI sound, e.g. FluidR3_GM.sf2)", value=env_now["SOUNDFONT_PATH"])
            k_sb = gr.Textbox(label="SUNO_API_BASE", value=env_now["SUNO_API_BASE"])
            k_sk = gr.Textbox(label="SUNO_API_KEY", type="password", value=env_now["SUNO_API_KEY"])
            k_d1 = gr.Checkbox(label="I have an active paid Suno plan that gives me ownership and commercial rights.",
                               value=env_now["SUNO_PAID_PLAN"].lower() in ("yes", "true", "1"))
            k_d2 = gr.Checkbox(label="I have accepted the Stability AI Community License and I am below its annual revenue limit.",
                               value=env_now["STABLE_AUDIO_LICENCE_ACCEPTED"].lower() in ("yes", "true", "1"))
            k_save = gr.Button("Save keys")
            k_msg = gr.Markdown()
            r = cfg.get("output_rights", {})
            gr.Markdown(f"### Credit on every output\n**Artist:** {r.get('artist')} &nbsp; **Owner:** {r.get('owner')} "
                        f"&nbsp; **Licence:** {r.get('licence')}  \n**Credit line:** {r.get('credit_line')}  \n"
                        "_Change these in `config/study.yaml` under `output_rights`. They are part of the "
                        "preregistered config, so change them before you register, not after._")

            def check():
                from .cli import cmd_check
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    cmd_check(root)
                return buf.getvalue()
            k_check.click(check, None, k_out)

            def save_keys(hf, sf, sb, sk, d1, d2):
                vals = {"HF_TOKEN": hf, "SOUNDFONT_PATH": sf, "SUNO_API_BASE": sb, "SUNO_API_KEY": sk,
                        "SUNO_PAID_PLAN": "yes" if d1 else "", "STABLE_AUDIO_LICENCE_ACCEPTED": "yes" if d2 else ""}
                env = root / ".env"
                lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else \
                    (root / ".env.example").read_text(encoding="utf-8").splitlines()
                seen, out = set(), []
                for line in lines:
                    k = line.split("=", 1)[0].strip()
                    if k in vals and not line.lstrip().startswith("#"):
                        out.append(f"{k}={vals[k]}")
                        seen.add(k)
                    else:
                        out.append(line)
                out += [f"{k}={v}" for k, v in vals.items() if k not in seen]
                env.write_text("\n".join(out) + "\n", encoding="utf-8")
                for k, v in vals.items():
                    if v:
                        os.environ[k] = v
                    else:
                        os.environ.pop(k, None)
                when = datetime.now(timezone.utc).isoformat(timespec="seconds")
                return f"Saved to `.env` at {when}. Declarations are recorded in each publish-mode manifest."
            k_save.click(save_keys, [k_hf, k_sf, k_sb, k_sk, k_d1, k_d2], k_msg)

        # ------------------------------------------------ About and cite
        with gr.Tab("About and cite"):
            gr.Markdown(f"""### {PROJECT_TITLE}
**Author:** {AUTHOR['name']} · ORCID [{AUTHOR['orcid'].rsplit('/', 1)[-1]}]({AUTHOR['orcid']})
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science, Brunel University London, UK; (2) Independent researcher.
*{AUTHOR['note']}*

**Licences:** code MIT · documents and benchmark CC BY 4.0 · generated music {r.get('licence')} with credit "{r.get('credit_line')}".

**How to cite:** PATEL, KEYUR SHAILESHKUMAR (2026). *{PROJECT_TITLE}* (Version {__version__}) [Computer software]. ORCID {AUTHOR['orcid']}.

**AI assistance statement:** This project was developed by KEYUR SHAILESHKUMAR PATEL with the help of an AI assistant (Claude, by Anthropic) for drafting text, writing and testing code, and literature search. All research decisions, the study design and the final content were chosen and approved by the author, who takes full responsibility for the work.

**Model terms also apply.** MusicGen weights are non-commercial, so Tattva publish mode refuses them. A notice cannot create copyright where the law gives none; see `docs/impact.pdf`.
""")

        # ------------------------------------------------ Help
        with gr.Tab("Help"):
            pdf = root / "docs" / "app_guide.pdf"
            gr.File(value=str(pdf) if pdf.exists() else None, label="Download this guide as PDF")
            gr.Markdown(guide_markdown(root))
    return demo


def futuristic_theme(gr):
    """Dark neon theme, used in both light and dark browser settings."""
    font = [gr.themes.GoogleFont("Space Grotesk"), "system-ui", "sans-serif"]
    mono = [gr.themes.GoogleFont("JetBrains Mono"), "monospace"]
    t = gr.themes.Base(primary_hue="violet", secondary_hue="cyan", neutral_hue="slate", font=font, font_mono=mono,
                       radius_size="lg")
    dark = dict(
        body_background_fill="#05060f", body_text_color="#e9ecff", body_text_color_subdued="#9aa3d6",
        background_fill_primary="rgba(12,15,32,0.85)", background_fill_secondary="rgba(18,22,44,0.7)",
        block_background_fill="rgba(18,22,44,0.62)", block_border_color="rgba(124,92,255,0.28)",
        block_label_text_color="#9aa3d6", block_title_text_color="#e9ecff", block_label_background_fill="rgba(10,12,30,0.7)",
        border_color_primary="rgba(124,92,255,0.35)", border_color_accent="#22e4ff",
        input_background_fill="rgba(6,8,20,0.85)", input_border_color="rgba(124,92,255,0.35)",
        input_border_color_focus="#22e4ff", input_placeholder_color="#5e679a",
        button_secondary_background_fill="rgba(30,34,70,0.8)", button_secondary_text_color="#e9ecff",
        button_secondary_border_color="rgba(124,92,255,0.4)",
        table_even_background_fill="rgba(14,17,36,0.9)", table_odd_background_fill="rgba(20,24,50,0.9)",
        table_border_color="rgba(124,92,255,0.25)", code_background_fill="rgba(2,4,12,0.9)",
        checkbox_background_color="rgba(6,8,20,0.9)", checkbox_label_background_fill="rgba(18,22,44,0.8)",
        checkbox_label_text_color="#e9ecff", color_accent_soft="rgba(139,92,255,0.25)",
        slider_color="#22e4ff", link_text_color="#22e4ff", link_text_color_hover="#ff4fd8",
    )
    t.set(**dark, **{k + "_dark": v for k, v in dark.items()})
    return t


def launch(root: Path, share: bool = False, port: int | None = None, host: str = "127.0.0.1"):
    import gradio as gr
    demo = build(root)
    theme = futuristic_theme(gr)
    kwargs = dict(share=share, server_port=port, server_name=host, allowed_paths=[str(root)])
    if int(gr.__version__.split(".")[0]) >= 6:
        kwargs.update(theme=theme, css=CSS)
    else:  # Gradio 4-5 take the look in Blocks; set it after building
        demo.theme, demo.css = theme, CSS
    demo.queue(default_concurrency_limit=2).launch(**kwargs)
