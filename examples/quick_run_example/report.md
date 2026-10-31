# Run report: Orchestral Input Pipeline: Structured Prompt Conditioning for Full-Ensemble AI Music Generation

> **Smoke test only.** Quick mode checks that the package works. Its numbers are not study results and must not be reported as findings.

**Author:** KEYUR SHAILESHKUMAR PATEL (ORCID https://orcid.org/0009-0008-5261-043X)  
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science, Brunel University London, UK; (2) Independent researcher  
*Conducted independently; not an official Brunel University London project.*

- Run: `20261028-224832_quick_f9df5d2c` (quick mode)
- Started 2026-10-28T22:48:32+00:00, finished 2026-10-28T22:48:38+00:00
- Config SHA-256: `f9df5d2c0a282994825eeb2c7f54774d7cd3e59a41449592b1124ad6f01d4998`
- Requests SHA-256: `78b651e6688c6520c115aa3448807a3faaf9803ee6078ecc7780dc60f1f6266c`
- Pieces evaluated: 8 (failed: 0)
- Human participants: none (fully computational study)
- Every file in this folder is listed with its SHA-256 hash in `SHA256SUMS`.

## Results in plain words

- midi: dynamics_accuracy could not be tested (4 pairs; the test needs at least 6).
- midi: structure_f could not be tested (4 pairs; the test needs at least 6).

## Mean scores by generator and condition

| generator | condition | dynamics_accuracy | structure_f | structure_chance | dynamic_range_db | range_violations |
| --- | --- | --- | --- | --- | --- | --- |
| midi | pipeline | 0.942 | 0.917 | 0.719 | 22.261 | 0.000 |
| midi | plain | -0.267 | 0.733 | 0.719 | 1.057 | 58.750 |

`structure_chance` is the boundary score expected from random boundaries; `structure_f` should be read against it.

## Confirmatory tests (preregistered)

| family | generator | comparison | metric | n_pairs | median_a | median_b | median_diff | ci95_low | ci95_high | W | p | p_holm | significant | rank_biserial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirmatory | midi | pipeline vs plain | dynamics_accuracy | 4 | 0.965 | -0.255 | 1.154 | 0.944 | 1.587 | - | - | - | None | 1.000 |
| confirmatory | midi | pipeline vs plain | structure_f | 4 | 1.000 | 0.667 | 0.167 | 0.000 | 0.400 | - | - | - | None | 1.000 |

## Secondary tests

| family | generator | comparison | metric | n_pairs | median_a | median_b | median_diff | ci95_low | ci95_high | W | p | p_holm | significant | rank_biserial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| secondary | midi | pipeline vs plain | dynamic_range_db | 4 | 20.498 | 1.179 | 19.056 | 17.401 | 29.304 | - | - | - | None | 1.000 |

## Agreement between measures (Spearman)

| measure_a | measure_b | n | spearman_rho | p |
| --- | --- | --- | --- | --- |
| dynamics_accuracy | structure_f | 8 | 0.548 | 0.160 |

## Intent-parser accuracy on the benchmark

Mean family F1 1.000, form correct 4/4, dynamic shape correct 4/4 (optimistic: rules were written with these requests).

Held-out requests: none yet (add them to config/heldout_requests.yaml before the main run).

## Frechet Audio Distance (CLAP embeddings, lower is closer to real recordings)

_No rows._

## Limitations

- All measures are automatic proxies for musical quality; no human listeners were involved.
- The AI judge is itself a model with its own biases; it is reported as a secondary measure only.
- CLAP similarities depend on the CLAP model's training data, which under-represents some styles (for example Indian classical music).
- Pieces are short (default 30 s), so large-scale form is tested only in compressed form.
- The intent parser was developed alongside the main benchmark; its accuracy there is optimistic. Parser accuracy on the held-out requests is the fair estimate.
- Closed services (Suno) cannot be re-run exactly and are excluded from confirmatory tests.

## Reproduce and verify

```
python run_all.py verify results/20261028-224832_quick_f9df5d2c
```
