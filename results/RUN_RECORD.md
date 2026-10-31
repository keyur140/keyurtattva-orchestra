# Complete Run Record: Orchestral Input Pipeline v0.1.0

**Study:** Orchestral Input Pipeline: Structured Prompt Conditioning for Full-Ensemble AI Music Generation
**Preregistration:** OSF, https://doi.org/10.17605/OSF.IO/AMBGF (osf.io/ambgf)
**Author:** KEYUR SHAILESHKUMAR PATEL. ORCID: https://orcid.org/0009-0008-5261-043X
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science, Brunel University London, UK; (2) Independent researcher
**Note:** Conducted independently; not an official Brunel University London project.
**Record written:** 2026-10-31, from the run logs, manifests and command outputs. All times are UTC.

---

## 1. Summary in one paragraph

The preregistered study package was downloaded from OSF, and its SHA-256 matched the registration.
It ran unchanged on one rented NVIDIA A100 80GB GPU (RunPod). All 1,152 music pieces were generated and
scored with 0 errors. The FAD reference set (52 real orchestral recordings) was downloaded and checked
against its frozen hashes. Every output file (2,655) passed its SHA-256 check on the GPU machine and again
on the laptop copy. One environment change was needed: an older version of the `transformers`
library, because the newest one broke CLAP scoring. No code or config was edited. Total cloud cost:
about $23.50.

---

## 2. Timeline (what was done, in order)

| Time (UTC) | Step |
|---|---|
| 2026-10-30 19:48 | Laptop checked: OpenSSH 9.5p2 present. New SSH key `C:\Users\Owner\.ssh\runpod_ed25519` (ed25519) created; only the public key was shared. |
| ~19:52 | `orchestra-pipeline-0.1.0.zip` (13,013,531 bytes) downloaded from the OSF registration to `Desktop\KeyurTattva\`. SHA-256 `8ae62267f0f0ecaec4c5f72da3af7a89d81aeafdfc99f880f12149c08d9ff0d8`, matching the registration. Extracted to `KeyurTattva\orchestra-pipeline` (117 files). |
| ~19:54 | RunPod Claude Code plugin (runpod@runpod 1.8.0) installed, following agents.runpod.io. |
| ~20:17 | Official RunPod CLI `runpodctl` v3.0.1 installed to `C:\Users\Owner\runpodctl\` (checksum matched the official release list). The author entered their own API key in PowerShell; it never passed through chat. |
| ~20:20 | Account checked: balance $30.00. GPU prices reviewed; author chose A100 80GB PCIe, secure cloud, $1.79/hr. |
| 20:24 | Author created pod `keyurtattva-study` (id `t82ton4f8kgmic`): template Runpod PyTorch 2.8.0 (`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`), 50 GB container disk, 100 GB volume at `/workspace`. |
| 20:34 | A duplicate pod (`thd1c6sfm2bxpf`) was created by mistake (the create command ran twice). It was noticed at ~21:55 and deleted by the author at ~22:02. It ran nothing (about $2.50 wasted). |
| ~20:35 | Pod reachable by SSH. GPU confirmed: NVIDIA A100 80GB PCIe (81,920 MiB). Python 3.12.3. |
| ~20:36 | Zip downloaded again directly on the pod from OSF. SHA-256 matched again. Unzipped. `python run_all.py verify .`: all 112 files matched their SHA-256 hashes. |
| ~20:37-20:47 | Python packages installed into a virtual environment `/workspace/venv` (reusing the image's PyTorch 2.8.0+cu128). The system Python blocks direct installs (PEP 668). |
| ~21:00-21:15 | Author accepted the Stable Audio Open licence on Hugging Face (affiliation: Independent researcher) and added their own read-only HF token to `.env` on the pod using a helper script. The token was never shown or sent in chat. Access check: logged in as `kp262`, Stable Audio Open download allowed. |
| ~21:18 | `python run_all.py check`: all libraries OK, GPU OK, HF_TOKEN set. |
| ~21:19 | `fetch-reference` failed: Freesound CDN returned HTTP 503 (server down). The backup source redirects to the same CDN. |
| 21:20 | **Model test 1** (`20261030-212049_full_7a8b2b82`; requests r01, r10; seed 11; 10 s pieces). All 16 pieces generated, then it **crashed in CLAP scoring**: `ValueError: You passed keyword argument 'audios' which is deprecated. Please use 'audio' instead.` (transformers 5.22.1). |
| ~21:57 | Fix, environment only: `transformers` 4.57.6, `huggingface_hub` 0.36.2, `diffusers` 0.39.0, `gradio` 6.17.3. All within the package's stated requirement ranges. `pip check`: no broken requirements. |
| 22:00 | **Model test 2** (`20261030-220005_full_7a8b2b82`). All 16 pieces generated and scored (CLAP and AI judge), 0 errors. The first run downloaded the 7B judge model (~20 min). Its automatic showcase step was stopped after 10 songs (test only). |
| 22:35:15 | **FULL STUDY RUN started**: `python run_all.py full`, run id `20261030-223515_full_7a8b2b82`. |
| 22:35 | Background FAD retry started (every 20 min; between failed attempts the reference folder was emptied so FAD could never use a partial set). |
| ~22:40 | Both model-test folders copied to the laptop. Test 2: all 53 files matched their SHA-256 hashes. |
| 2026-10-30 23:24 | FAD reference download **succeeded**: all 52 frozen recordings passed their SHA-256 checks, and ATTRIBUTION.md was written. |
| 22:35 - 06:20 | Generation: MusicGen (~50 s per 30-s piece), then Stable Audio Open, then MIDI. Then scoring of all 1,152 pieces. |
| 2026-10-31 06:20:59 | Study part finished: 1,152 OK, 0 failed. Tables, statistics, report.pdf/html/md and SHA256SUMS written. |
| 06:21 - ~07:05 | Showcase: 15/15 KeyurTattva songs made (3 refined versions each, best kept). |
| ~07:39 | `run_all.py verify results/20261030-223515_full_7a8b2b82`: all 2,655 files OK. |
| ~07:40 - 07:55 | Everything copied to the laptop (tar over SSH, ~4.2 GB). |
| ~07:55 | Laptop hash check: full run 2,655 matched, 0 mismatched, 0 missing. Showcase 213 matched, 0 mismatched, 0 missing. |
| ~07:57 | Pod **stopped** (not deleted). GPU billing ended. Balance $6.50. |

Note: the laptop slept from about 23:57 to 00:57 and from 03:30 to 07:35, so status updates paused. The pod run was not affected.

---

## 3. Hardware and software (from the run manifest)

- **GPU:** 1x NVIDIA A100 80GB PCIe, CUDA 12.8 (RunPod secure cloud, pod `t82ton4f8kgmic`)
- **System:** Linux 6.8.0, x86_64, 128 CPUs visible, Python 3.12.3
- **Packages:** torch 2.8.0+cu128, transformers 4.57.6, diffusers 0.39.0, accelerate 1.15.0, numpy 2.1.2, scipy 1.18.1, pandas 3.1.0, librosa 1.0.0, soundfile 0.14.0, pretty_midi 0.2.11.post0, PyYAML 6.0.3, reportlab 5.1.0 (full list in `pod_pip_freeze.txt`)
- **Models:**
  - MusicGen: `facebook/musicgen-medium`, revision `d3bd7b00761b78ad7a8a05145ee31e7832e9916c`, guidance 3.0, 32 kHz
  - Stable Audio Open: `stabilityai/stable-audio-open-1.0`, 100 steps, guidance 7.0, 44.1 kHz (no revision recorded in the manifest)
  - MIDI route: rule-based symbolic composer, built-in additive synth, no soundfont
  - CLAP: `laion/larger_clap_music`, revision `a0b4534a14f58e20944452dff00a22a06ce629d1`, 10-s windows
  - AI judge: `Qwen/Qwen2-Audio-7B-Instruct`, revision `0a095220c30b7b31434169c3086508ef3ea5bf0a`, greedy decoding, rubric v1
- **Integrity hashes:**
  - Study zip: `8ae62267f0f0ecaec4c5f72da3af7a89d81aeafdfc99f880f12149c08d9ff0d8`
  - config_sha256: `7a8b2b82226ba1fe0b6ebe6120b84108140d8ad4df0a166e24f1cc3137a80a1a`
  - requests_sha256: `78b651e6688c6520c115aa3448807a3faaf9803ee6078ecc7780dc60f1f6266c`
  - heldout_requests_sha256: `22e9fec7d5edeeb34755775f011baf8464b86f995c2a7783941e1ecb5a42b3ad`
  - SHA256SUMS of the run folder (the file itself): `2569113c26db3391b851afaf57c9174cbbb25b8ebd436ff5bc40906bed38be3e`

---

## 4. Study design as run (registered defaults, unchanged)

- 48 requests x 3 seeds (11, 22, 33), 30-second pieces
- Conditions: plain, expert, pipeline (MIDI route: plain and pipeline only)
- Generators: MusicGen, Stable Audio Open, MIDI route. Suno disabled (as registered)
- Pieces: 432 MusicGen + 432 Stable Audio + 288 MIDI = **1,152**
- Statistics: Wilcoxon signed-rank on per-request means, Holm correction, alpha 0.05, bootstrap 95% CI (10,000 resamples, seed 20261027)
- Confirmatory: pipeline vs plain on prompt_adherence, section_clarity, dynamics_accuracy, structure_f, per generator

---

## 5. Main results

### 5.1 Confirmatory tests (pipeline vs plain, Holm-corrected)

| Generator | Measure | Median diff | 95% CI | p (Holm) | Supported? |
|---|---|---|---|---|---|
| MIDI | prompt_adherence | +0.0077 | [0.0053, 0.0141] | 7.1e-11 | **Yes** (r = 0.96) |
| MIDI | section_clarity | -0.167 | [-0.222, -0.067] | 0.559 | No |
| MIDI | dynamics_accuracy | +0.920 | [0.874, 0.946] | 1.4e-12 | **Yes** (r = 1.00) |
| MIDI | structure_f | +0.200 | [0.111, 0.236] | 0.00013 | **Yes** (r = 0.77) |
| MusicGen | prompt_adherence | -0.0019 | [-0.0033, -0.0003] | 0.015 | **No: opposite direction** (r = -0.51) |
| MusicGen | section_clarity | 0.000 | [-0.063, 0.056] | 1.0 | No |
| MusicGen | dynamics_accuracy | -0.084 | [-0.181, 0.017] | 0.720 | No |
| MusicGen | structure_f | +0.097 | [0.000, 0.111] | 1.0 | No |
| Stable Audio | prompt_adherence | -0.0034 | [-0.0047, -0.0010] | 0.015 | **No: opposite direction** (r = -0.51) |
| Stable Audio | section_clarity | +0.056 | [-0.095, 0.125] | 1.0 | No |
| Stable Audio | dynamics_accuracy | -0.009 | [-0.117, 0.132] | 1.0 | No |
| Stable Audio | structure_f | 0.000 | [-0.067, 0.083] | 1.0 | No |

**Count:** MIDI 3/4 supported; MusicGen 0/4 (1 significant in the opposite direction); Stable Audio 0/4 (1 significant in the opposite direction).

### 5.2 In easy words

- When the pipeline **writes the music itself** (MIDI route), it follows the request much better: dynamics, structure and text match all improve, with very large effects.
- When the pipeline can only **send a prompt** to a text-to-audio AI (MusicGen, Stable Audio), the extra detail is mostly not followed, and the long structured prompt matches the request text slightly *less* well than a plain prompt (CLAP).
- Main message: *structure helps when you control the score; prompts alone do not carry it.*

### 5.3 Secondary results (selected; full table in tables/hypothesis_tests.csv)

- Pipeline vs expert, prompt adherence: lower for MusicGen (p_holm 0.0009) and Stable Audio (p_holm 0.0037).
- Dynamic range: MIDI pipeline +22.2 dB vs plain (p_holm 4e-14); Stable Audio expert +9.5 dB vs plain (p_holm 1.8e-05); pipeline lower than expert for MusicGen (-3.7 dB) and Stable Audio (-7.8 dB).
- Cultural similarity (n = 10): MIDI pipeline higher (p_holm 0.029); Stable Audio pipeline lower (p_holm 0.039).

### 5.4 FAD (descriptive; lower = closer to real orchestral recordings; 52 reference tracks)

| Generator | plain | expert | pipeline |
|---|---|---|---|
| MIDI | 0.0984 | - | **0.0229** |
| MusicGen | 0.0279 | 0.0427 | 0.0268 |
| Stable Audio | 0.0236 | 0.0285 | **0.0105** |

### 5.5 Parser accuracy

- Study requests (r01-r48): 48/48 perfect (family F1 1.0, form correct, shape correct).
- Held-out requests (h01-h15, written later): mean family F1 0.70; form correct 12/15; dynamics shape correct 3/15.

### 5.6 AI judge

The judge gave nearly identical scores to every piece: overall 7 (1,152/1,152), adherence 8, orchestration 7, structure 7, dynamics 7 (768) or 6 (384).
It could not tell pieces apart, so judge comparisons are zero by construction. **Report as a limitation.**

---

## 6. Deviations and transparency notes

1. **Library versions (environment only):** transformers 5.22.1 broke CLAP scoring (test 1 crash). Replaced with transformers 4.57.6 (allowed: >=4.45), which moved huggingface_hub to 0.36.2, diffusers to 0.39.0 and gradio to 6.17.3. No code changed. The versions are recorded in the manifest.
2. **Model test 1 failed** and is kept in `model_check` as a record.
3. **FAD reference:** delayed by a Freesound outage, then fetched and fully verified before the metrics stage. No deviation in the final data.
4. **Showcase of test 2** was stopped early (test only; not study data).
5. No code, config, request or showcase file was edited. Every run used the registered configuration.

Full detail: `DEVIATIONS_NOTES.txt`.

---

## 7. Costs

| Item | Cost |
|---|---|
| Study pod (A100 80GB PCIe secure, $1.79/hr + storage), ~11.5 h | ~$21 |
| Duplicate pod by mistake (~1.5 h) | ~$2.50 |
| **Total spent** | **~$23.50** of $30.00 |
| Remaining balance | $6.50 |
| Storage while the stopped pod is kept | ~$0.03/hr (~$0.67/day) until deleted |

---

## 8. Where everything is (laptop)

`C:\Users\Owner\OneDrive\Desktop\KeyurTattva\`
- `orchestra-pipeline-0.1.0.zip`: registered package (unchanged)
- `orchestra-pipeline\`: extracted package (unchanged)
- `power_settings_before.txt`: laptop sleep settings before the run
- `results\`
  - `20261030-223515_full_7a8b2b82\`: **the full study** (report.pdf / .html / .md, tables\, audio\ with 1,152 pieces, prompts\, specs\, logs\, manifest.json, pieces.jsonl, OUTPUT_LICENSE.md, SHA256SUMS)
  - `showcase\showcase_20261031-062141_full\`: 15 showcase songs plus SHA256SUMS_from_pod.txt
  - `model_check\`: test 1 (failed) and test 2, plus their console logs
  - `DEVIATIONS_NOTES.txt`: deviations for OSF
  - `RUN_RECORD.md`: this file
  - `20261030-223515_full_7a8b2b82_console_full.log`: full console output
  - `fad_reference_retry.log`, `fad_reference_ATTRIBUTION.md`: FAD reference download log and credits
  - `pod_pip_freeze.txt`: exact Python package list
  - `verify_copy.ps1`: script to re-check any run folder against its SHA256SUMS

---

## 9. Open items for the author

1. Restore the laptop sleep setting: `powercfg /change standby-timeout-ac 10`
2. After checking the laptop copy, delete the stopped pod to end the storage fee:
   `C:\Users\Owner\runpodctl\runpodctl.exe pod delete t82ton4f8kgmic`
3. Optional: delete the Hugging Face token (huggingface.co/settings/tokens) and the RunPod API key (console.runpod.io/user/settings) if they are no longer needed.
4. Upload the results and deviation notes to OSF as the registration's results/update.

---

*How to cite:* PATEL, KEYUR SHAILESHKUMAR (2026). Orchestral Input Pipeline: Structured Prompt Conditioning for Full-Ensemble AI Music Generation (v0.1.0). Preregistration: https://doi.org/10.17605/OSF.IO/AMBGF. ORCID https://orcid.org/0009-0008-5261-043X
