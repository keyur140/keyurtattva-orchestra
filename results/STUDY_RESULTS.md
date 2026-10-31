# Study results: registered full run 20261030-223515

**Study:** Orchestral Input Pipeline: Structured Prompt Conditioning for Full-Ensemble AI Music Generation (v0.1.0)
**Preregistration:** https://doi.org/10.17605/OSF.IO/AMBGF
**Author:** KEYUR SHAILESHKUMAR PATEL. ORCID: https://orcid.org/0009-0008-5261-043X
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science, Brunel University London, UK; (2) Independent researcher
**Note:** Conducted independently; not an official Brunel University London project.

This `results/` folder holds the outputs of the preregistered full run, made with the unchanged v0.1.0 package (the repository root, tag `v0.1.0`).
The package's own `results/README.md` is left exactly as registered. The package's `verify` treats everything else in `results/` as run output, so `python run_all.py verify .` still passes on this repository.

**Windows users:** clone with `git clone -c core.autocrlf=false <repo-url>`. Otherwise Git may convert line endings, and the SHA-256 checks would then fail.

## What is here

| Path | Contents |
|---|---|
| `20261030-223515_full_7a8b2b82/` | The full run: `report.pdf` / `report.html` / `report.md`, `tables/` (hypothesis tests, FAD, parser accuracy, per-piece scores), `manifest.json`, `pieces.jsonl`, `prompts/`, `specs/`, `logs/`, all MIDI `.mid` files, and `SHA256SUMS` for **every** file of the run, including the audio that is not stored here |
| `audio_samples/` | 8 sample pieces from the full run: request r01, seed 11, one per generator x condition (see below) |
| `showcase/` | The 15 KeyurTattva showcase songs (3 refined versions each, WAV) with their reports, plus `SHA256SUMS_from_pod.txt` |
| `model_check/` | The two pre-study technical checks: test 1 (crashed in CLAP scoring; kept as a record) and test 2 (passed), without audio |
| `DEVIATIONS_NOTES.txt` | Everything that differed from the plan (one environment change; no code or config edits) |
| `RUN_RECORD.md` | Complete record: timeline, hardware, software, model revisions, results, costs |
| `fad_reference_ATTRIBUTION.md`, `fad_reference_retry.log` | Credits and download log for the 52 FAD reference recordings (MTG-Jamendo; not redistributed) |
| `pod_pip_freeze.txt` | Exact Python packages used on the GPU machine |
| `20261030-223515_full_7a8b2b82_console_full.log` | Full console output of the run |
| `verify_copy.ps1` | Re-checks a run folder against its `SHA256SUMS` (Windows PowerShell) |

## Audio that is NOT in git

The full run made 1,152 pieces (about 4 GB of WAV), which is too large for GitHub.
They will be deposited on **Zenodo under CC BY-NC 4.0**, and the link will be added here.
`20261030-223515_full_7a8b2b82/SHA256SUMS` lists the SHA-256 of every one of those files, so any copy can be checked.
Run against this folder alone, `verify_copy.ps1` reports the audio files as missing, which is expected; after you add the Zenodo audio back into `audio/`, every file should match.

## The 8 audio samples

All from request **r01**, seed **11**, 30 seconds. The original path is shown in brackets; each file's hash is in `20261030-223515_full_7a8b2b82/SHA256SUMS`.

| File | Generator | Condition | Original path |
|---|---|---|---|
| `musicgen__r01_plain_s11.wav` | MusicGen | plain | `audio/musicgen/r01_plain_s11.wav` |
| `musicgen__r01_expert_s11.wav` | MusicGen | expert | `audio/musicgen/r01_expert_s11.wav` |
| `musicgen__r01_pipeline_s11.wav` | MusicGen | pipeline | `audio/musicgen/r01_pipeline_s11.wav` |
| `stable_audio__r01_plain_s11.wav` | Stable Audio Open | plain | `audio/stable_audio/r01_plain_s11.wav` |
| `stable_audio__r01_expert_s11.wav` | Stable Audio Open | expert | `audio/stable_audio/r01_expert_s11.wav` |
| `stable_audio__r01_pipeline_s11.wav` | Stable Audio Open | pipeline | `audio/stable_audio/r01_pipeline_s11.wav` |
| `midi__r01_plain_s11.wav` | MIDI route | plain | `audio/midi/r01_plain_s11.wav` |
| `midi__r01_pipeline_s11.wav` | MIDI route | pipeline | `audio/midi/r01_pipeline_s11.wav` |

## Licences

- Generated music and results: CC BY-NC 4.0 (see each run's `OUTPUT_LICENSE.md`). Credit: "Music by KeyurTattva (KEYUR SHAILESHKUMAR PATEL)".
- Code: MIT (see `LICENSE` at the repository root). Documents: CC BY 4.0 (see `LICENSE-DOCS.md`).
- The FAD reference recordings are not included; see `fad_reference_ATTRIBUTION.md` for their credits and licences.

## How to cite

PATEL, KEYUR SHAILESHKUMAR (2026). *Orchestral Input Pipeline: Structured Prompt Conditioning for Full-Ensemble AI Music Generation* (v0.1.0). Preregistration: https://doi.org/10.17605/OSF.IO/AMBGF. ORCID: https://orcid.org/0009-0008-5261-043X. See also `CITATION.cff` at the repository root.
