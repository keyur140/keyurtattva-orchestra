# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Fast checks (no neural models needed): run with  python -m pytest -q"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orchestra.analysis import boundary_f, dynamics_accuracy  # noqa: E402
from orchestra.clap import frechet_distance, presence_auc  # noqa: E402
from orchestra.compiler import compile_prompt  # noqa: E402
from orchestra.conductor import conduct, dynamics_curve, shape_marks  # noqa: E402
from orchestra.instruments import INSTRUMENTS  # noqa: E402
from orchestra.intent import family_f1, parse_request  # noqa: E402
from orchestra.judge import parse_judgement  # noqa: E402
from orchestra.lyrics import count_syllables, lyric_fit, parse_lyrics  # noqa: E402
from orchestra.orchestrator import orchestrate  # noqa: E402
from orchestra.provenance import sha256_text, verify_sums, write_sums  # noqa: E402
from orchestra.stats import holm, rank_biserial  # noqa: E402

FULL = "A heroic overture for full symphony orchestra that starts quietly and ends with full brass and timpani."


def test_parser_full_orchestra():
    s = parse_request("t", FULL)
    assert s.families == ["strings", "woodwinds", "brass", "percussion"]
    assert s.form == "overture" and s.dynamics_shape == "crescendo"
    assert "timpani" in s.instruments


def test_parser_raga_and_culture():
    s = parse_request("t", "Raga Yaman with sitar, tabla and bansuri, slow alap building to a fast jhala.")
    assert s.scale == "raga_yaman" and s.form == "raga_form" and s.families == ["world"]


def test_parser_bass_drum_is_not_double_bass():
    s = parse_request("t", "A march for brass, snare drum and bass drum.")
    assert "bass_drum" in s.instruments and "double_bass" not in s.instruments


def test_parser_matches_benchmark_targets():
    reqs = yaml.safe_load((ROOT / "config" / "requests.yaml").read_text())["requests"]
    assert len(reqs) == 48 and len({r["id"] for r in reqs}) == 48
    f1 = np.mean([family_f1(parse_request(r["id"], r["text"]).families, r["targets"]["families"]) for r in reqs])
    assert f1 > 0.9


def test_orchestrator_registers_inside_ranges():
    plan = orchestrate(parse_request("t", FULL))
    for p in plan.parts:
        ins = INSTRUMENTS[p.instrument]
        if not ins.is_drum:
            assert ins.low <= p.register_low <= p.register_high <= ins.high
    assert plan.lead == "violin" and plan.bass == "double_bass"


def test_fold_into_range():
    tuba = INSTRUMENTS["tuba"]
    assert tuba.in_range(tuba.fold_into_range(84))


def test_shapes():
    assert shape_marks("crescendo", 4)[0] == "pp" and shape_marks("crescendo", 4)[-1] == "ff"
    assert shape_marks("decrescendo", 4)[-1] == "pp"
    arch = shape_marks("arch", 5)
    assert arch.index(max(arch, key=["pp", "p", "mp", "mf", "f", "ff", "fff"].index)) not in (0, 4)


def test_prompt_budget_and_conditions():
    s = parse_request("t", FULL)
    plan, secs = orchestrate(s), conduct(s, 30)
    assert compile_prompt("plain", s, plan, secs) == FULL
    assert "high quality" in compile_prompt("expert", s, plan, secs)
    for budget in (40, 60, 90):
        assert len(compile_prompt("pipeline", s, plan, secs, budget).split()) <= budget


def test_dynamics_accuracy_and_curve():
    s = parse_request("t", FULL)
    curve = dynamics_curve(conduct(s, 30), 30)
    assert len(curve) == 30 and curve[-1] > curve[0]
    assert dynamics_accuracy(curve, curve) == pytest.approx(1.0)
    assert math.isnan(dynamics_accuracy(curve, np.zeros(30)))


def test_boundary_f():
    assert boundary_f([10.0, 20.0], [10.5, 19.0]) == 1.0
    assert boundary_f([5.0], [10.0, 20.0]) == 0.0
    assert boundary_f([10.0], [10.0, 20.0]) == pytest.approx(2 / 3)


def test_presence_auc_and_fad():
    assert presence_auc({"a": 0.9, "b": 0.1, "c": 0.2}, ["a"]) == 1.0
    assert presence_auc({"a": 0.1, "b": 0.9}, ["a"]) == 0.0
    rng = np.random.default_rng(0)
    x = rng.normal(size=(200, 8))
    assert frechet_distance(x, x) == pytest.approx(0.0, abs=1e-6)
    assert frechet_distance(x, x + 3) > 50


def test_stats_helpers():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert rank_biserial(np.array([1.0, 2.0, 3.0])) == 1.0
    assert rank_biserial(np.array([-1.0, -2.0])) == -1.0


def test_judge_parsing():
    j = parse_judgement('Sure: {"adherence": 7, "orchestration": 6, "dynamics": 5, "structure": 6, '
                        '"overall": 6, "advice": "louder brass"}')
    assert j["adherence"] == 7 and j["advice"] == "louder brass"
    assert math.isnan(parse_judgement("no idea")["overall"])


def test_lyrics():
    secs = parse_lyrics("[verse]\nI walk along the river\nunder silver light\n[chorus]\nSing it loud tonight")
    assert [s.tag for s in secs] == ["verse", "chorus"]
    assert count_syllables("under silver light") == 5
    assert 0 <= lyric_fit(secs, 100, 4)["fit"] <= 1
    with pytest.raises(ValueError):
        parse_lyrics("[banana]\nhello")


def test_hashing(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("y")
    write_sums(tmp_path)
    assert verify_sums(tmp_path) == (2, [])
    (tmp_path / "a.txt").write_text("changed")
    assert verify_sums(tmp_path)[1] == ["changed: a.txt"]
    assert sha256_text("abc").startswith("ba7816bf")


@pytest.fixture()
def no_model_config(tmp_path):
    cfg = yaml.safe_load((ROOT / "config" / "study.yaml").read_text())
    cfg["study"]["metrics"]["clap"]["enabled"] = False
    cfg["study"]["metrics"]["judge"]["enabled"] = False
    cfg["quick"]["metrics"]["clap"] = False
    p = tmp_path / "study.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return p


def test_quick_run_end_to_end(tmp_path, no_model_config):
    pytest.importorskip("pretty_midi")
    pytest.importorskip("librosa")
    from orchestra.runner import run_study
    run = run_study(ROOT, no_model_config, "quick", tmp_path / "results",
                    {"request_ids": ["r01", "r15"], "duration_s": 8}, log=lambda *_: None)
    for name in ("report.md", "report.html", "manifest.json", "SHA256SUMS", "tables/pieces.csv"):
        assert (run / name).exists()
    assert verify_sums(run)[1] == []


def test_song_mode_three_versions(tmp_path, no_model_config):
    pytest.importorskip("pretty_midi")
    from orchestra.song import run_song
    lyr = tmp_path / "my_song.txt"
    lyr.write_text("[verse]\nUnder the evening sky we rise\n[chorus]\nSing with the strings tonight\n")
    out = run_song(ROOT, no_model_config, "A romantic song for strings, harp and choir that builds",
                   lyrics_path=str(lyr), versions=3, generator="midi", duration=8, judge=False,
                   out_dir=tmp_path / "songs", log=lambda *_: None)
    for v in (1, 2, 3):
        assert (out / f"v{v}.wav").exists()
    assert (out / "BEST.txt").exists() and (out / "lyrics.txt").exists()
    assert verify_sums(out)[1] == []


def test_rights_stamp(tmp_path):
    import soundfile as sf
    from orchestra.rights import DEFAULT_RIGHTS, stamp_wav, write_output_licence
    wav = tmp_path / "x.wav"
    sf.write(str(wav), np.zeros(1000, dtype=np.float32), 8000)
    stamp_wav(wav, DEFAULT_RIGHTS, "test")
    stamp_wav(wav, DEFAULT_RIGHTS, "test")  # idempotent: replaces, never duplicates
    raw = wav.read_bytes()
    assert raw.count(b"IART") == 1 and b"KeyurTattva" in raw
    assert sf.info(str(wav)).frames == 1000
    assert "KeyurTattva" in write_output_licence(tmp_path, DEFAULT_RIGHTS, ["m"]).read_text()


def test_publish_blocks_research_only_models(monkeypatch):
    from orchestra.publish import PublishBlocked, check_publish
    with pytest.raises(PublishBlocked):
        check_publish("musicgen")
    monkeypatch.delenv("SUNO_PAID_PLAN", raising=False)
    with pytest.raises(PublishBlocked):
        check_publish("suno")  # needs your declaration first
    monkeypatch.setenv("SUNO_PAID_PLAN", "yes")
    assert check_publish("suno")["declarations"]
    assert check_publish("midi")["generator"] == "midi"


def test_publish_mode_release_pack(tmp_path, no_model_config):
    pytest.importorskip("pretty_midi")
    from orchestra.song import run_song
    out = run_song(ROOT, no_model_config, "A heroic fanfare for brass and timpani", versions=2,
                   generator="midi", duration=6, judge=False, out_dir=tmp_path / "songs",
                   log=lambda *_: None, purpose="publish")
    for name in ("RELEASE_CHECKLIST.md", "AI_DISCLOSURE.txt", "HUMAN_CONTRIBUTIONS.md"):
        assert (out / name).exists()
    assert "Tattva publish" in (out / "OUTPUT_LICENSE.md").read_text()
    assert b"Tattva publish mode" in (out / "v1.wav").read_bytes()
    (out / "HUMAN_CONTRIBUTIONS.md").write_text("I re-mixed it.\n")  # editing it must not break verify
    assert verify_sums(out)[1] == []


def test_explore_marked_not_cleared(tmp_path, no_model_config):
    pytest.importorskip("pretty_midi")
    from orchestra.song import run_song
    out = run_song(ROOT, no_model_config, "A calm string piece", versions=1, generator="midi",
                   duration=5, judge=False, out_dir=tmp_path / "songs", log=lambda *_: None)
    assert b"not cleared for release" in (out / "v1.wav").read_bytes()
    assert not (out / "RELEASE_CHECKLIST.md").exists()


def test_same_seed_same_song_across_processes(tmp_path):
    """Reproducibility: two separate Python processes must write byte-identical MIDI."""
    pytest.importorskip("pretty_midi")
    import subprocess, sys
    code = ("import sys; sys.path.insert(0, 'src'); from pathlib import Path; "
            "from orchestra.intent import parse_request; from orchestra.orchestrator import orchestrate; "
            "from orchestra.conductor import conduct; from orchestra.generators.midi import MidiGenerator; "
            "s = parse_request('t', 'A romantic Bollywood song with strings, bansuri and choir that builds'); "
            "g = MidiGenerator(); out = Path(sys.argv[1]); "
            "g.generate(condition='pipeline', prompt='', seed=11, duration=8, out_wav=out, spec=s, "
            "plan=orchestrate(s), sections=conduct(s, 8))")
    digests = []
    for i, hs in enumerate(("1", "2")):
        out = tmp_path / f"a{i}.wav"
        env = {**__import__("os").environ, "PYTHONHASHSEED": hs}
        subprocess.run([sys.executable, "-c", code, str(out)], cwd=ROOT, env=env, check=True)
        from orchestra.provenance import sha256_file
        digests.append(sha256_file(out.with_suffix(".mid")))
    assert digests[0] == digests[1]


def test_app_builds_and_plans():
    pytest.importorskip("gradio")
    from orchestra.app import build, lyric_check, preview, purpose_banner
    assert build(ROOT) is not None
    summary, parts, secs, plot, plain, expert, pipe, full = preview(
        "An epic trailer cue for full orchestra and choir growing to a huge climax", 30, "musicgen")
    assert len(parts) > 5 and len(secs) >= 3 and len(pipe.split()) <= 90
    msg, table = lyric_check("[verse]\nUnder the evening sky we rise\n", "A romantic song")
    assert "lines fit" in msg and len(table) == 1
    assert "Blocked" in purpose_banner("Tattva publish", "musicgen")
    assert "not cleared" in purpose_banner("Explore", "musicgen")


def test_fad_reference_list_is_frozen_and_consistent():
    from orchestra.reference import _archive_for, read_list
    tars, rows = read_list(ROOT / "config" / "fad_reference.tsv")
    assert len(rows) == 52 and len(tars) == 2
    for r in rows:
        assert len(r["sha256"]) == 64 and r["licence"].startswith("http://creativecommons.org/")
        assert _archive_for(r["file"], tars) in tars


def test_fetch_reference_verifies_hashes(tmp_path):
    import hashlib
    import io
    import tarfile
    from orchestra.reference import ReferenceError, fetch_reference
    src = tmp_path / "src"
    src.mkdir()
    data = {"00/1.low.mp3": b"one", "00/2.low.mp3": b"two"}
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for name, content in data.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
    (src / "raw_30s_audio-low-00.tar").write_bytes(buf.getvalue())
    tar_sha = hashlib.sha256(buf.getvalue()).hexdigest()

    def make_root(track_sha):
        root = tmp_path / f"root_{track_sha[:4]}"
        (root / "config").mkdir(parents=True)
        lines = [f"# tar raw_30s_audio-low-00.tar {tar_sha}", "track_id\tfile\tduration_s\tsha256\tlicence\tcredit"]
        lines += [f"t{i}\t{n}\t30\t{track_sha if i == 0 else hashlib.sha256(c).hexdigest()}\thttp://creativecommons.org/licenses/by/3.0/\tTrack {i}"
                  for i, (n, c) in enumerate(data.items())]
        (root / "config" / "fad_reference.tsv").write_text("\n".join(lines) + "\n")
        return root

    good = make_root(hashlib.sha256(b"one").hexdigest())
    out = fetch_reference(good, base_url=src.as_uri() + "/", log=lambda *_: None)
    assert sorted(p.name for p in out.glob("*.mp3")) == ["1.low.mp3", "2.low.mp3"]
    assert "Licence: http://creativecommons.org/licenses/by/3.0/" in (out / "ATTRIBUTION.md").read_text()
    assert not (good / "data" / "cache" / "raw_30s_audio-low-00.tar").exists()

    bad = make_root("0" * 64)
    with pytest.raises(ReferenceError):
        fetch_reference(bad, base_url=src.as_uri() + "/", log=lambda *_: None)


def test_showcase_makes_songs_and_index(tmp_path, no_model_config):
    from orchestra.showcase import load_showcase, run_showcase
    sc = load_showcase(ROOT)
    held = yaml.safe_load((ROOT / "config" / "heldout_requests.yaml").read_text())["requests"]
    assert [s["request"] for s in sc["songs"]] == [r["text"] for r in held]
    out = run_showcase(ROOT, no_model_config, "quick", out_dir=tmp_path, only=["h15"], generator="midi",
                       versions=1, duration=6, log=lambda *_: None)
    index = (out / "SHOWCASE.md").read_text()
    assert "Price of a Soul" in index and "| ok |" in index
    assert verify_sums(out)[1] == []


def _sung_tune(path, seq=((60, .5), (62, .5), (64, .5), (65, .5), (67, 1.0), (65, .5), (64, .5), (62, .5), (60, 1.0))):
    """A synthetic 'voice': harmonic tone with vibrato, soft attacks and short breaths."""
    import soundfile as sf
    sr, parts = 22050, []
    for p, d in seq:
        t = np.arange(int(sr * d)) / sr
        f = 440 * 2 ** ((p - 69) / 12) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t))
        ph = 2 * np.pi * np.cumsum(f) / sr
        env = np.minimum(1, np.minimum(t / 0.03, (d - t) / 0.05))
        parts += [(np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * env * 0.5, np.zeros(int(sr * 0.04))]
    y = np.concatenate(parts)
    sf.write(str(path), y + np.random.default_rng(0).normal(0, 0.003, y.size), sr)
    return path


def test_voice_tune_is_heard_note_by_note(tmp_path):
    from orchestra.voice import extract_melody
    m = extract_melody(_sung_tune(tmp_path / "tune.wav"))
    assert [p for _, _, p in m.notes] == [60, 62, 64, 65, 67, 65, 64, 62, 60]
    assert m.key_name == "C major" and 70 <= m.tempo <= 140 and not m.warnings


def test_song_follows_sung_tune_and_credits_the_singer(tmp_path, no_model_config):
    import json
    import pretty_midi
    from orchestra.song import run_song
    out = run_song(ROOT, no_model_config, "A heroic fanfare for brass and timpani", versions=1, generator="midi",
                   duration=10, out_dir=tmp_path, log=lambda *_: None, purpose="publish",
                   voice_tune=str(_sung_tune(tmp_path / "tune.wav")))
    man = json.loads((out / "manifest.json").read_text())
    assert man["voice_note"]["tune"]["key"] == "C major"
    assert man["spec"]["tonic"] == 0 and man["spec"]["scale"] == "major"
    assert (out / "voice_tune.wav").exists() and (out / "your_tune.mid").exists()
    pm = pretty_midi.PrettyMIDI(str(out / "v1.mid"))
    seq = [n.pitch % 12 for i in pm.instruments for n in sorted(i.notes, key=lambda n: n.start)]
    tune = [0, 2, 4, 5, 7, 5, 4, 2, 0]
    assert any(seq[k:k + 3] == tune[:3] for k in range(len(seq)))  # the theme opens with your first notes
    assert "sang the main tune myself" in (out / "HUMAN_CONTRIBUTIONS.md").read_text()
    assert "Your voice note" in (out / "song_report.md").read_text()


def test_voice_lyrics_become_sections(tmp_path, no_model_config, monkeypatch):
    import orchestra.voice as voice
    from orchestra.lyrics import parse_lyrics
    from orchestra.song import run_song
    text = ("I walk alone through the city at night, the lights are calling me home. "
            "Nobody knows the fire in my heart, but I keep it burning strong.")
    lyr = voice.transcript_to_lyrics(text)
    assert parse_lyrics(lyr) and lyr.startswith("[Verse 1]")
    monkeypatch.setattr(voice, "transcribe", lambda path, model_id=None, language=None:
                        {"text": text, "model": "test-whisper", "language": "en", "source_sha256": "0" * 64})
    out = run_song(ROOT, no_model_config, "A calm string piece", versions=1, generator="midi", duration=6,
                   out_dir=tmp_path, log=lambda *_: None, voice_lyrics=str(_sung_tune(tmp_path / "words.wav")))
    assert (out / "transcript.txt").read_text().strip() == text
    assert "fire in my heart" in (out / "lyrics.txt").read_text()
    assert "your voice note" in (out / "song_report.md").read_text()


def test_publish_blocks_musicgen_melody():
    from orchestra.publish import PublishBlocked, check_publish
    with pytest.raises(PublishBlocked):
        check_publish("musicgen_melody")
