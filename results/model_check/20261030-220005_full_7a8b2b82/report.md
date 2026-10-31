# Run report: Orchestral Input Pipeline: Structured Prompt Conditioning for Full-Ensemble AI Music Generation

**Author:** KEYUR SHAILESHKUMAR PATEL (ORCID https://orcid.org/0009-0008-5261-043X)  
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science, Brunel University London, UK; (2) Independent researcher  
*Conducted independently; not an official Brunel University London project.*

- Run: `20261030-220005_full_7a8b2b82` (full mode)
- Started 2026-10-30T22:00:05+00:00, finished 2026-10-30T22:04:24+00:00
- Config SHA-256: `7a8b2b82226ba1fe0b6ebe6120b84108140d8ad4df0a166e24f1cc3137a80a1a`
- Requests SHA-256: `78b651e6688c6520c115aa3448807a3faaf9803ee6078ecc7780dc60f1f6266c`
- Pieces evaluated: 16 (failed: 0)
- Human participants: none (fully computational study)
- Every file in this folder is listed with its SHA-256 hash in `SHA256SUMS`.

## Results in plain words

- midi: prompt_adherence could not be tested (2 pairs; the test needs at least 6).
- midi: section_clarity could not be tested (2 pairs; the test needs at least 6).
- midi: dynamics_accuracy could not be tested (2 pairs; the test needs at least 6).
- midi: structure_f could not be tested (2 pairs; the test needs at least 6).
- musicgen: prompt_adherence could not be tested (2 pairs; the test needs at least 6).
- musicgen: section_clarity could not be tested (2 pairs; the test needs at least 6).
- musicgen: dynamics_accuracy could not be tested (2 pairs; the test needs at least 6).
- musicgen: structure_f could not be tested (2 pairs; the test needs at least 6).
- stable_audio: prompt_adherence could not be tested (2 pairs; the test needs at least 6).
- stable_audio: section_clarity could not be tested (2 pairs; the test needs at least 6).
- stable_audio: dynamics_accuracy could not be tested (2 pairs; the test needs at least 6).
- stable_audio: structure_f could not be tested (2 pairs; the test needs at least 6).

## Mean scores by generator and condition

| generator | condition | prompt_adherence | section_clarity | dynamics_accuracy | structure_f | structure_chance | judge_overall | dynamic_range_db | range_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| midi | pipeline | 0.008 | 0.518 | 0.952 | 0.733 | 0.761 | 7.000 | 20.976 | 0.000 |
| midi | plain | -0.005 | 0.339 | -0.400 | 0.833 | 0.761 | 7.000 | 2.164 | 38.500 |
| musicgen | expert | 0.009 | 0.277 | 0.008 | 0.733 | 0.761 | 7.000 | 14.279 | - |
| musicgen | pipeline | 0.010 | 0.268 | 0.408 | 0.633 | 0.761 | 7.000 | 5.769 | - |
| musicgen | plain | 0.003 | 0.714 | 0.358 | 0.833 | 0.761 | 7.000 | 12.450 | - |
| stable_audio | expert | 0.005 | 0.312 | -0.655 | 0.733 | 0.761 | 7.000 | 39.289 | - |
| stable_audio | pipeline | 0.008 | 0.375 | -0.406 | 0.900 | 0.761 | 7.000 | 32.505 | - |
| stable_audio | plain | 0.007 | 0.219 | -0.442 | 0.900 | 0.761 | 7.000 | 38.418 | - |

`structure_chance` is the boundary score expected from random boundaries; `structure_f` should be read against it.

## Confirmatory tests (preregistered)

| family | generator | comparison | metric | n_pairs | median_a | median_b | median_diff | ci95_low | ci95_high | W | p | p_holm | significant | rank_biserial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirmatory | midi | pipeline vs plain | prompt_adherence | 2 | 0.008 | -0.005 | 0.014 | 0.005 | 0.023 | - | - | - | None | 1.000 |
| confirmatory | midi | pipeline vs plain | section_clarity | 2 | 0.518 | 0.339 | 0.179 | -0.143 | 0.500 | - | - | - | None | 0.333 |
| confirmatory | midi | pipeline vs plain | dynamics_accuracy | 2 | 0.952 | -0.400 | 1.352 | 1.176 | 1.527 | - | - | - | None | 1.000 |
| confirmatory | midi | pipeline vs plain | structure_f | 2 | 0.733 | 0.833 | -0.100 | -0.200 | 0.000 | - | - | - | None | -1.000 |
| confirmatory | musicgen | pipeline vs plain | prompt_adherence | 2 | 0.010 | 0.003 | 0.006 | 0.00046 | 0.012 | - | - | - | None | 1.000 |
| confirmatory | musicgen | pipeline vs plain | section_clarity | 2 | 0.268 | 0.714 | -0.446 | -0.750 | -0.143 | - | - | - | None | -1.000 |
| confirmatory | musicgen | pipeline vs plain | dynamics_accuracy | 2 | 0.408 | 0.358 | 0.050 | -0.733 | 0.833 | - | - | - | None | 0.333 |
| confirmatory | musicgen | pipeline vs plain | structure_f | 2 | 0.633 | 0.833 | -0.200 | -0.400 | 0.000 | - | - | - | None | -1.000 |
| confirmatory | stable_audio | pipeline vs plain | prompt_adherence | 2 | 0.008 | 0.007 | 0.002 | -0.000553 | 0.004 | - | - | - | None | 0.333 |
| confirmatory | stable_audio | pipeline vs plain | section_clarity | 2 | 0.375 | 0.219 | 0.156 | 0.000 | 0.312 | - | - | - | None | 1.000 |
| confirmatory | stable_audio | pipeline vs plain | dynamics_accuracy | 2 | -0.406 | -0.442 | 0.036 | -0.145 | 0.218 | - | - | - | None | 0.333 |
| confirmatory | stable_audio | pipeline vs plain | structure_f | 2 | 0.900 | 0.900 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |

## Secondary tests

| family | generator | comparison | metric | n_pairs | median_a | median_b | median_diff | ci95_low | ci95_high | W | p | p_holm | significant | rank_biserial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| secondary | musicgen | pipeline vs expert | prompt_adherence | 2 | 0.010 | 0.009 | 0.000472 | -0.000129 | 0.001 | - | - | - | None | 0.333 |
| secondary | musicgen | pipeline vs expert | section_clarity | 2 | 0.268 | 0.277 | -0.009 | -0.143 | 0.125 | - | - | - | None | -0.333 |
| secondary | musicgen | pipeline vs expert | dynamics_accuracy | 2 | 0.408 | 0.008 | 0.400 | -0.033 | 0.833 | - | - | - | None | 0.333 |
| secondary | musicgen | pipeline vs expert | structure_f | 2 | 0.633 | 0.733 | -0.100 | -0.200 | 0.000 | - | - | - | None | -1.000 |
| secondary | musicgen | pipeline vs expert | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | musicgen | pipeline vs expert | cultural_similarity | 1 | 0.013 | 0.012 | 0.000993 | - | - | - | - | - | None | 1.000 |
| secondary | musicgen | pipeline vs expert | dynamic_range_db | 2 | 5.769 | 14.279 | -8.510 | -8.666 | -8.354 | - | - | - | None | -1.000 |
| secondary | musicgen | expert vs plain | prompt_adherence | 2 | 0.009 | 0.003 | 0.006 | -0.000613 | 0.012 | - | - | - | None | 0.333 |
| secondary | musicgen | expert vs plain | section_clarity | 2 | 0.277 | 0.714 | -0.438 | -0.875 | 0.000 | - | - | - | None | -1.000 |
| secondary | musicgen | expert vs plain | dynamics_accuracy | 2 | 0.008 | 0.358 | -0.350 | -1.567 | 0.867 | - | - | - | None | -0.333 |
| secondary | musicgen | expert vs plain | structure_f | 2 | 0.733 | 0.833 | -0.100 | -0.200 | 0.000 | - | - | - | None | -1.000 |
| secondary | musicgen | expert vs plain | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | musicgen | expert vs plain | cultural_similarity | 1 | 0.012 | 0.013 | -0.00058 | - | - | - | - | - | None | -1.000 |
| secondary | musicgen | expert vs plain | dynamic_range_db | 2 | 14.279 | 12.450 | 1.828 | -6.967 | 10.624 | - | - | - | None | 0.333 |
| secondary | stable_audio | pipeline vs expert | prompt_adherence | 2 | 0.008 | 0.005 | 0.003 | -7.85e-05 | 0.007 | - | - | - | None | 0.333 |
| secondary | stable_audio | pipeline vs expert | section_clarity | 2 | 0.375 | 0.312 | 0.062 | 0.000 | 0.125 | - | - | - | None | 1.000 |
| secondary | stable_audio | pipeline vs expert | dynamics_accuracy | 2 | -0.406 | -0.655 | 0.248 | 0.158 | 0.339 | - | - | - | None | 1.000 |
| secondary | stable_audio | pipeline vs expert | structure_f | 2 | 0.900 | 0.733 | 0.167 | 0.000 | 0.333 | - | - | - | None | 1.000 |
| secondary | stable_audio | pipeline vs expert | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | stable_audio | pipeline vs expert | cultural_similarity | 1 | 0.010 | 0.010 | -7.26e-05 | - | - | - | - | - | None | -1.000 |
| secondary | stable_audio | pipeline vs expert | dynamic_range_db | 2 | 32.505 | 39.289 | -6.785 | -10.059 | -3.510 | - | - | - | None | -1.000 |
| secondary | stable_audio | expert vs plain | prompt_adherence | 2 | 0.005 | 0.007 | -0.002 | -0.003 | -0.000474 | - | - | - | None | -1.000 |
| secondary | stable_audio | expert vs plain | section_clarity | 2 | 0.312 | 0.219 | 0.094 | 0.000 | 0.188 | - | - | - | None | 1.000 |
| secondary | stable_audio | expert vs plain | dynamics_accuracy | 2 | -0.655 | -0.442 | -0.212 | -0.303 | -0.121 | - | - | - | None | -1.000 |
| secondary | stable_audio | expert vs plain | structure_f | 2 | 0.733 | 0.900 | -0.167 | -0.333 | 0.000 | - | - | - | None | -1.000 |
| secondary | stable_audio | expert vs plain | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | stable_audio | expert vs plain | cultural_similarity | 1 | 0.010 | 0.011 | -0.000476 | - | - | - | - | - | None | -1.000 |
| secondary | stable_audio | expert vs plain | dynamic_range_db | 2 | 39.289 | 38.418 | 0.872 | -0.797 | 2.540 | - | - | - | None | 0.333 |
| secondary | midi | pipeline vs plain | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | midi | pipeline vs plain | cultural_similarity | 1 | 0.013 | 0.008 | 0.005 | - | - | - | - | - | None | 1.000 |
| secondary | midi | pipeline vs plain | dynamic_range_db | 2 | 20.976 | 2.164 | 18.812 | 18.300 | 19.324 | - | - | - | None | 1.000 |
| secondary | midi | pipeline vs plain | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | musicgen | pipeline vs plain | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | musicgen | pipeline vs plain | cultural_similarity | 1 | 0.013 | 0.013 | 0.000413 | - | - | - | - | - | None | 1.000 |
| secondary | musicgen | pipeline vs plain | dynamic_range_db | 2 | 5.769 | 12.450 | -6.681 | -15.321 | 1.958 | - | - | - | None | -0.333 |
| secondary | musicgen | pipeline vs plain | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | stable_audio | pipeline vs plain | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | stable_audio | pipeline vs plain | cultural_similarity | 1 | 0.010 | 0.011 | -0.000548 | - | - | - | - | - | None | -1.000 |
| secondary | stable_audio | pipeline vs plain | dynamic_range_db | 2 | 32.505 | 38.418 | -5.913 | -7.519 | -4.306 | - | - | - | None | -1.000 |
| secondary | stable_audio | pipeline vs plain | judge_overall | 2 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |

## Agreement between measures (Spearman)

| measure_a | measure_b | n | spearman_rho | p |
| --- | --- | --- | --- | --- |
| prompt_adherence | section_clarity | 16 | -0.384 | 0.142 |
| prompt_adherence | dynamics_accuracy | 16 | 0.065 | 0.812 |
| prompt_adherence | structure_f | 16 | -0.492 | 0.053 |
| section_clarity | dynamics_accuracy | 16 | 0.221 | 0.410 |
| section_clarity | structure_f | 16 | 0.034 | 0.902 |
| dynamics_accuracy | structure_f | 16 | -0.091 | 0.739 |

## Intent-parser accuracy on the benchmark

Mean family F1 1.000, form correct 2/2, dynamic shape correct 2/2 (optimistic: rules were written with these requests).

Held-out requests: mean family F1 0.703, form correct 12/15, shape correct 3/15.

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
python run_all.py verify results/20261030-220005_full_7a8b2b82
```
