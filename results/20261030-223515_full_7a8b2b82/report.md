# Run report: Orchestral Input Pipeline: Structured Prompt Conditioning for Full-Ensemble AI Music Generation

**Author:** KEYUR SHAILESHKUMAR PATEL (ORCID https://orcid.org/0009-0008-5261-043X)  
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science, Brunel University London, UK; (2) Independent researcher  
*Conducted independently; not an official Brunel University London project.*

- Run: `20261030-223515_full_7a8b2b82` (full mode)
- Started 2026-10-30T22:35:15+00:00, finished 2026-10-31T06:20:59+00:00
- Config SHA-256: `7a8b2b82226ba1fe0b6ebe6120b84108140d8ad4df0a166e24f1cc3137a80a1a`
- Requests SHA-256: `78b651e6688c6520c115aa3448807a3faaf9803ee6078ecc7780dc60f1f6266c`
- Pieces evaluated: 1152 (failed: 0)
- Human participants: none (fully computational study)
- Every file in this folder is listed with its SHA-256 hash in `SHA256SUMS`.

## Results in plain words

- midi: the pipeline condition scored higher than plain on prompt_adherence (median difference 0.008, 95% CI 0.005 to 0.014, Holm-adjusted p = 7.07e-11, effect size r = 0.957, 48 requests): a statistically significant difference.
- midi: the pipeline condition scored lower than plain on section_clarity (median difference -0.167, 95% CI -0.222 to -0.067, Holm-adjusted p = 0.559, effect size r = -0.293, 48 requests): no significant difference.
- midi: the pipeline condition scored higher than plain on dynamics_accuracy (median difference 0.920, 95% CI 0.874 to 0.946, Holm-adjusted p = 1.36e-12, effect size r = 1.000, 44 requests): a statistically significant difference.
- midi: the pipeline condition scored higher than plain on structure_f (median difference 0.200, 95% CI 0.111 to 0.236, Holm-adjusted p = 0.000129, effect size r = 0.772, 48 requests): a statistically significant difference.
- musicgen: the pipeline condition scored lower than plain on prompt_adherence (median difference -0.002, 95% CI -0.003 to -0.000324, Holm-adjusted p = 0.015, effect size r = -0.507, 48 requests): a statistically significant difference.
- musicgen: the pipeline condition scored equal than plain on section_clarity (median difference 0.000, 95% CI -0.062 to 0.056, Holm-adjusted p = 1.000, effect size r = 0.014, 48 requests): no significant difference.
- musicgen: the pipeline condition scored lower than plain on dynamics_accuracy (median difference -0.084, 95% CI -0.181 to 0.017, Holm-adjusted p = 0.720, effect size r = -0.271, 44 requests): no significant difference.
- musicgen: the pipeline condition scored higher than plain on structure_f (median difference 0.097, 95% CI 0.000 to 0.111, Holm-adjusted p = 1.000, effect size r = 0.152, 48 requests): no significant difference.
- stable_audio: the pipeline condition scored lower than plain on prompt_adherence (median difference -0.003, 95% CI -0.005 to -0.001, Holm-adjusted p = 0.015, effect size r = -0.510, 48 requests): a statistically significant difference.
- stable_audio: the pipeline condition scored higher than plain on section_clarity (median difference 0.056, 95% CI -0.095 to 0.125, Holm-adjusted p = 1.000, effect size r = 0.129, 48 requests): no significant difference.
- stable_audio: the pipeline condition scored lower than plain on dynamics_accuracy (median difference -0.009, 95% CI -0.117 to 0.132, Holm-adjusted p = 1.000, effect size r = 0.026, 44 requests): no significant difference.
- stable_audio: the pipeline condition scored equal than plain on structure_f (median difference 0.000, 95% CI -0.067 to 0.083, Holm-adjusted p = 1.000, effect size r = -0.075, 48 requests): no significant difference.

## Mean scores by generator and condition

| generator | condition | prompt_adherence | section_clarity | dynamics_accuracy | structure_f | structure_chance | judge_overall | dynamic_range_db | range_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| midi | pipeline | 0.007 | 0.515 | 0.911 | 0.571 | 0.391 | 7.000 | 21.645 | 0.000 |
| midi | plain | -0.006 | 0.588 | 0.004 | 0.397 | 0.391 | 7.000 | 1.745 | 96.597 |
| musicgen | expert | 0.007 | 0.477 | -0.044 | 0.484 | 0.391 | 7.000 | 16.051 | - |
| musicgen | pipeline | 0.004 | 0.474 | 0.024 | 0.438 | 0.391 | 7.000 | 10.289 | - |
| musicgen | plain | 0.006 | 0.473 | 0.090 | 0.416 | 0.391 | 7.000 | 12.645 | - |
| stable_audio | expert | 0.005 | 0.469 | -0.061 | 0.412 | 0.391 | 7.000 | 36.812 | - |
| stable_audio | pipeline | 0.002 | 0.487 | -0.004 | 0.393 | 0.391 | 7.000 | 30.674 | - |
| stable_audio | plain | 0.005 | 0.450 | 0.002 | 0.413 | 0.391 | 7.000 | 27.627 | - |

`structure_chance` is the boundary score expected from random boundaries; `structure_f` should be read against it.

## Confirmatory tests (preregistered)

| family | generator | comparison | metric | n_pairs | median_a | median_b | median_diff | ci95_low | ci95_high | W | p | p_holm | significant | rank_biserial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirmatory | midi | pipeline vs plain | prompt_adherence | 48 | 0.007 | -0.002 | 0.008 | 0.005 | 0.014 | 25.000 | 6.42e-12 | 7.07e-11 | True | 0.957 |
| confirmatory | midi | pipeline vs plain | section_clarity | 48 | 0.490 | 0.632 | -0.167 | -0.222 | -0.067 | 398.500 | 0.080 | 0.559 | False | -0.293 |
| confirmatory | midi | pipeline vs plain | dynamics_accuracy | 44 | 0.942 | 0.005 | 0.920 | 0.874 | 0.946 | 0.000 | 1.14e-13 | 1.36e-12 | True | 1.000 |
| confirmatory | midi | pipeline vs plain | structure_f | 48 | 0.667 | 0.422 | 0.200 | 0.111 | 0.236 | 103.000 | 1.29e-05 | 0.000129 | True | 0.772 |
| confirmatory | musicgen | pipeline vs plain | prompt_adherence | 48 | 0.005 | 0.007 | -0.002 | -0.003 | -0.000324 | 290.000 | 0.002 | 0.015 | True | -0.507 |
| confirmatory | musicgen | pipeline vs plain | section_clarity | 48 | 0.494 | 0.469 | 0.000 | -0.062 | 0.056 | 533.000 | 0.935 | 1.000 | False | 0.014 |
| confirmatory | musicgen | pipeline vs plain | dynamics_accuracy | 44 | 0.005 | 0.077 | -0.084 | -0.181 | 0.017 | 361.000 | 0.120 | 0.720 | False | -0.271 |
| confirmatory | musicgen | pipeline vs plain | structure_f | 48 | 0.444 | 0.444 | 0.097 | 0.000 | 0.111 | 347.500 | 0.399 | 1.000 | False | 0.152 |
| confirmatory | stable_audio | pipeline vs plain | prompt_adherence | 48 | 0.004 | 0.006 | -0.003 | -0.005 | -0.001 | 288.000 | 0.002 | 0.015 | True | -0.510 |
| confirmatory | stable_audio | pipeline vs plain | section_clarity | 48 | 0.500 | 0.467 | 0.056 | -0.095 | 0.125 | 491.500 | 0.443 | 1.000 | False | 0.129 |
| confirmatory | stable_audio | pipeline vs plain | dynamics_accuracy | 44 | -0.027 | 0.021 | -0.009 | -0.117 | 0.132 | 482.000 | 0.885 | 1.000 | False | 0.026 |
| confirmatory | stable_audio | pipeline vs plain | structure_f | 48 | 0.444 | 0.444 | 0.000 | -0.067 | 0.083 | 325.000 | 0.688 | 1.000 | False | -0.075 |

## Secondary tests

| family | generator | comparison | metric | n_pairs | median_a | median_b | median_diff | ci95_low | ci95_high | W | p | p_holm | significant | rank_biserial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| secondary | musicgen | pipeline vs expert | prompt_adherence | 48 | 0.005 | 0.007 | -0.003 | -0.004 | -0.001 | 206.000 | 4.19e-05 | 0.000921 | True | -0.650 |
| secondary | musicgen | pipeline vs expert | section_clarity | 48 | 0.494 | 0.478 | 0.022 | -0.078 | 0.122 | 554.000 | 0.727 | 1.000 | False | 0.058 |
| secondary | musicgen | pipeline vs expert | dynamics_accuracy | 44 | 0.005 | -0.006 | 0.101 | -0.101 | 0.165 | 429.000 | 0.448 | 1.000 | False | 0.133 |
| secondary | musicgen | pipeline vs expert | structure_f | 48 | 0.444 | 0.444 | 0.000 | -0.111 | 0.111 | 290.500 | 0.069 | 0.961 | False | -0.325 |
| secondary | musicgen | pipeline vs expert | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | musicgen | pipeline vs expert | cultural_similarity | 10 | 0.009 | 0.010 | -0.001 | -0.003 | 0.002 | 17.000 | 0.322 | 1.000 | False | -0.382 |
| secondary | musicgen | pipeline vs expert | dynamic_range_db | 48 | 8.850 | 14.122 | -3.691 | -6.940 | -2.233 | 184.000 | 1.25e-05 | 0.000287 | True | -0.687 |
| secondary | musicgen | expert vs plain | prompt_adherence | 48 | 0.007 | 0.007 | 0.001 | 0.000449 | 0.001 | 361.000 | 0.019 | 0.307 | False | 0.386 |
| secondary | musicgen | expert vs plain | section_clarity | 48 | 0.478 | 0.469 | -0.022 | -0.083 | 0.056 | 539.500 | 0.795 | 1.000 | False | -0.043 |
| secondary | musicgen | expert vs plain | dynamics_accuracy | 44 | -0.006 | 0.077 | -0.150 | -0.264 | -0.025 | 286.000 | 0.014 | 0.237 | False | -0.422 |
| secondary | musicgen | expert vs plain | structure_f | 48 | 0.444 | 0.444 | 0.056 | 0.000 | 0.111 | 141.500 | 0.008 | 0.137 | False | 0.524 |
| secondary | musicgen | expert vs plain | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | musicgen | expert vs plain | cultural_similarity | 10 | 0.010 | 0.010 | -0.000648 | -0.002 | 0.001 | 23.000 | 0.695 | 1.000 | False | -0.164 |
| secondary | musicgen | expert vs plain | dynamic_range_db | 48 | 14.122 | 10.285 | 2.243 | 0.385 | 4.665 | 329.000 | 0.007 | 0.137 | False | 0.440 |
| secondary | stable_audio | pipeline vs expert | prompt_adherence | 48 | 0.004 | 0.006 | -0.003 | -0.004 | -0.000993 | 235.000 | 0.000177 | 0.004 | True | -0.600 |
| secondary | stable_audio | pipeline vs expert | section_clarity | 48 | 0.500 | 0.450 | 0.014 | -0.103 | 0.144 | 530.000 | 0.719 | 1.000 | False | 0.060 |
| secondary | stable_audio | pipeline vs expert | dynamics_accuracy | 44 | -0.027 | -0.124 | 0.079 | -0.059 | 0.197 | 351.000 | 0.094 | 1.000 | False | 0.291 |
| secondary | stable_audio | pipeline vs expert | structure_f | 48 | 0.444 | 0.389 | 0.000 | -0.111 | 0.000 | 354.500 | 0.816 | 1.000 | False | -0.043 |
| secondary | stable_audio | pipeline vs expert | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | stable_audio | pipeline vs expert | cultural_similarity | 10 | 0.006 | 0.010 | -0.003 | -0.007 | 0.000366 | 8.000 | 0.049 | 0.732 | False | -0.709 |
| secondary | stable_audio | pipeline vs expert | dynamic_range_db | 48 | 31.176 | 37.357 | -7.801 | -10.568 | -4.408 | 241.000 | 0.000234 | 0.005 | True | -0.590 |
| secondary | stable_audio | expert vs plain | prompt_adherence | 48 | 0.006 | 0.006 | -6.07e-05 | -0.001 | 0.002 | 515.000 | 0.461 | 1.000 | False | 0.124 |
| secondary | stable_audio | expert vs plain | section_clarity | 48 | 0.450 | 0.467 | 0.000 | -0.044 | 0.083 | 458.000 | 0.666 | 1.000 | False | 0.075 |
| secondary | stable_audio | expert vs plain | dynamics_accuracy | 44 | -0.124 | 0.021 | -0.041 | -0.113 | 0.027 | 368.000 | 0.141 | 1.000 | False | -0.257 |
| secondary | stable_audio | expert vs plain | structure_f | 48 | 0.389 | 0.444 | 0.000 | -0.089 | 0.083 | 360.500 | 0.884 | 1.000 | False | -0.027 |
| secondary | stable_audio | expert vs plain | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | stable_audio | expert vs plain | cultural_similarity | 10 | 0.010 | 0.008 | -0.000105 | -0.002 | 0.003 | 27.000 | 1.000 | 1.000 | False | 0.018 |
| secondary | stable_audio | expert vs plain | dynamic_range_db | 48 | 37.357 | 27.661 | 9.543 | 5.341 | 13.237 | 140.000 | 7.71e-07 | 1.85e-05 | True | 0.762 |
| secondary | midi | pipeline vs plain | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | midi | pipeline vs plain | cultural_similarity | 10 | 0.010 | 0.001 | 0.007 | 0.003 | 0.014 | 2.000 | 0.006 | 0.029 | True | 0.927 |
| secondary | midi | pipeline vs plain | dynamic_range_db | 48 | 23.679 | 1.777 | 22.208 | 19.166 | 23.758 | 0.000 | 7.11e-15 | 4.26e-14 | True | 1.000 |
| secondary | midi | pipeline vs plain | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | musicgen | pipeline vs plain | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | musicgen | pipeline vs plain | cultural_similarity | 10 | 0.009 | 0.010 | -0.001 | -0.003 | 0.000887 | 16.000 | 0.275 | 0.279 | False | -0.418 |
| secondary | musicgen | pipeline vs plain | dynamic_range_db | 48 | 8.850 | 10.285 | -1.835 | -5.479 | 0.635 | 375.000 | 0.028 | 0.085 | False | -0.362 |
| secondary | musicgen | pipeline vs plain | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | stable_audio | pipeline vs plain | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |
| secondary | stable_audio | pipeline vs plain | cultural_similarity | 10 | 0.006 | 0.008 | -0.004 | -0.006 | -0.000984 | 3.000 | 0.010 | 0.039 | True | -0.891 |
| secondary | stable_audio | pipeline vs plain | dynamic_range_db | 48 | 31.176 | 27.661 | 3.517 | -1.241 | 5.725 | 443.000 | 0.139 | 0.279 | False | 0.247 |
| secondary | stable_audio | pipeline vs plain | judge_overall | 48 | 7.000 | 7.000 | 0.000 | 0.000 | 0.000 | - | - | - | None | 0.000 |

## Agreement between measures (Spearman)

| measure_a | measure_b | n | spearman_rho | p |
| --- | --- | --- | --- | --- |
| prompt_adherence | section_clarity | 1152 | -0.000693 | 0.981 |
| prompt_adherence | dynamics_accuracy | 1056 | -0.009 | 0.775 |
| prompt_adherence | structure_f | 1152 | 0.034 | 0.254 |
| prompt_adherence | judge_dynamics | 1152 | -0.105 | 0.000345 |
| section_clarity | dynamics_accuracy | 1056 | -0.005 | 0.875 |
| section_clarity | structure_f | 1152 | -0.063 | 0.033 |
| section_clarity | judge_dynamics | 1152 | -0.058 | 0.050 |
| dynamics_accuracy | structure_f | 1056 | 0.066 | 0.031 |
| dynamics_accuracy | judge_dynamics | 1056 | -0.012 | 0.688 |
| structure_f | judge_dynamics | 1152 | 0.056 | 0.056 |

## Intent-parser accuracy on the benchmark

Mean family F1 1.000, form correct 48/48, dynamic shape correct 48/48 (optimistic: rules were written with these requests).

Held-out requests: mean family F1 0.703, form correct 12/15, shape correct 3/15.

## Frechet Audio Distance (CLAP embeddings, lower is closer to real recordings)

| generator | condition | n | n_reference | fad_clap |
| --- | --- | --- | --- | --- |
| midi | pipeline | 144 | 52 | 0.023 |
| midi | plain | 144 | 52 | 0.098 |
| musicgen | expert | 144 | 52 | 0.043 |
| musicgen | pipeline | 144 | 52 | 0.027 |
| musicgen | plain | 144 | 52 | 0.028 |
| stable_audio | expert | 144 | 52 | 0.028 |
| stable_audio | pipeline | 144 | 52 | 0.011 |
| stable_audio | plain | 144 | 52 | 0.024 |

## Limitations

- All measures are automatic proxies for musical quality; no human listeners were involved.
- The AI judge is itself a model with its own biases; it is reported as a secondary measure only.
- CLAP similarities depend on the CLAP model's training data, which under-represents some styles (for example Indian classical music).
- Pieces are short (default 30 s), so large-scale form is tested only in compressed form.
- The intent parser was developed alongside the main benchmark; its accuracy there is optimistic. Parser accuracy on the held-out requests is the fair estimate.
- Closed services (Suno) cannot be re-run exactly and are excluded from confirmatory tests.

## Reproduce and verify

```
python run_all.py verify results/20261030-223515_full_7a8b2b82
```
