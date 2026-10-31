# OSF Preregistration (draft): Orchestral Input Pipeline

**Template:** OSF Preregistration (standard pre-data-collection template), adapted for a
fully computational study.

**Title:** Structured, score-like input conditioning for full-ensemble AI music generation:
a preregistered computational comparison of plain, expert and pipeline prompts

**Author:** KEYUR SHAILESHKUMAR PATEL, ORCID https://orcid.org/0009-0008-5261-043X
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science,
Brunel University London, UK; (2) Independent researcher.
*Conducted independently; not an official Brunel University London project.*

**AI assistance statement:** This project was developed by KEYUR SHAILESHKUMAR PATEL with the help of an AI assistant (Claude, by Anthropic) for drafting text, writing and testing code, and literature search. All research decisions, the study design and the final content were chosen and approved by the author, who takes full responsibility for the work.

**Status:** READY TO REGISTER (all items filled in on 30 October 2026). Submit on OSF **before** running
`python run_all.py full`. Quick-mode smoke tests may be run before registration; their
outputs are not analysed.

---

## 1. Study information

### 1.1 Research questions
- RQ1. Does a score-structured input pipeline (orchestration engine + conductor layer +
  prompt compiler) improve the measurable quality of generated orchestral music compared
  with the user's plain request?
- RQ2. Does it improve on an "expert" prompt (the request plus quality tags that
  experienced users add)?
- RQ3. How well do automatic metrics and an AI audio judge agree with each other?
- RQ4 (exploratory). Does the iterative refinement loop (song mode) improve successive
  versions of the same piece?

### 1.2 Hypotheses (confirmatory)
For each reproducible generator g in {MusicGen-medium, Stable Audio Open 1.0, symbolic
MIDI route}, comparing the **pipeline** condition with the **plain** condition
(two-sided tests):

| ID | Measure | Hypothesis |
| --- | --- | --- |
| H1 | Prompt adherence (CLAP cosine similarity between the audio and the original request) | pipeline differs from plain; expected direction: higher |
| H2 | Section clarity (AUC: requested instrument families score above non-requested ones, CLAP zero-shot, per-generator z-scored) | pipeline differs from plain; expected: higher |
| H3 | Dynamics accuracy (Spearman correlation between measured loudness over time and the target dynamic plan) | pipeline differs from plain; expected: higher |
| H4 | Structure (boundary F-measure, +/-2 s, against the target form's section boundaries) | pipeline differs from plain; expected: higher |

4 measures x 3 generators = 12 confirmatory tests, corrected together with the Holm
method at alpha = 0.05.

For the MIDI route, "plain" is the applicant's original v1 generator logic (random scale
notes, every instrument always playing, fixed velocity); there is no expert condition.

## 2. Design plan

- **Study type:** computational experiment; no human or animal participants; no personal data.
- **Blinding:** not applicable; all measures are automatic. The AI judge receives the
  original request and the audio, never the condition label or the compiled prompt.
- **Design:** within-request, repeated measures. Factors: condition (plain, expert,
  pipeline) x generator, with 3 random seeds per cell.
- **Randomisation:** fixed seeds 11, 22, 33 for every cell, so results can be re-run.

## 3. Sampling plan

- **Existing data:** none of the outcome data exist at registration time.
- **Requests:** the 48 requests in `config/requests.yaml` (SHA-256
  `78b651e6688c6520c115aa3448807a3faaf9803ee6078ecc7780dc60f1f6266c (version 0.1.0; update if you change the file)`), covering strings, woodwinds, brass, percussion, keyboards and
  harp, voices and choir, Indian instruments, and hybrid electronic sounds; forms
  including overture, sonata, rondo, variations, film cue, song, march, chorale and raga.
  Each request has author-written targets (families, form, dynamic shape).
- **Held-out requests for the parser:** 15 requests in `config/heldout_requests.yaml`
  (SHA-256 `22e9fec7d5edeeb34755775f011baf8464b86f995c2a7783941e1ecb5a42b3ad`), written after the parser rules were frozen. They come from the
  author's own KeyurTattva song descriptions written before this project, condensed into one
  sentence each with AI assistance (lyrics and artist names left out); targets follow the
  conventions of `config/requests.yaml` and were accepted by the author. All 15 are songs,
  mostly rap and Indian fusion, so this estimate covers that style and tests form only for
  "song"; it is reported descriptively alongside the main-benchmark parser accuracy.
- **Sample size:** 48 requests x 3 seeds x (3 conditions x 2 audio models + 2 MIDI
  conditions) = 1,152 pieces of 30 s. The unit of analysis is the request (seeds averaged),
  so each test has up to 48 pairs.
- **Sensitivity:** with 48 pairs, a two-sided Wilcoxon signed-rank test has about 80%
  power to detect a standardised paired effect of about d = 0.41 at alpha = 0.05 and about
  d = 0.55 at the strictest Holm threshold (0.05/12). Smaller effects may be missed.
- **Stopping rule:** the run ends when every planned piece has been generated or has
  failed after one retry.

## 4. Variables

- **Manipulated:** input condition (plain, expert, pipeline); generator.
- **Measured (confirmatory):** prompt adherence, section clarity, dynamics accuracy,
  structure F (definitions in the hypothesis table and in `src/orchestra/`).
- **Measured (secondary):** AI judge ratings 1-10 (adherence, orchestration, dynamics,
  structure, overall; Qwen2-Audio-7B-Instruct, greedy decoding, fixed rubric); cultural
  similarity (CLAP, 10 culture-tagged requests); dynamic range (dB); Frechet Audio
  Distance on CLAP embeddings against 52 real orchestral recordings from the MTG-Jamendo
  dataset (Bogdanov et al., 2019), fixed in `config/fad_reference.tsv` (SHA-256
  `e0123088fa40fdf5367545c8667ef5eec9f0654088e0410e13295f99e09424d1`): every track tagged genre---orchestral plus classical, symphonic,
  orchestra, strings or violin in archive folders 00 and 62, each with its own SHA-256 and
  Creative Commons licence, fetched with `python run_all.py fetch-reference` into
  `data/reference_orchestral` (descriptive; non-commercial research use; audio not redistributed); range violations (MIDI route); parser
  accuracy.
- **Fixed settings:** `config/study.yaml` (SHA-256 `7a8b2b82226ba1fe0b6ebe6120b84108140d8ad4df0a166e24f1cc3137a80a1a (version 0.1.0; update if you change the file)`); software version
  the SHA-256 of `orchestra-pipeline-0.1.0.zip` as uploaded with this registration
  (stated in the registration form, because a file cannot contain its own hash).

## 5. Analysis plan

- **Confirmatory test:** for each generator and measure, the per-request difference
  (pipeline minus plain) is tested with a two-sided Wilcoxon signed-rank test
  (zero_method = "wilcox"). Holm correction across the 12 tests; alpha = 0.05.
- **Effect sizes:** matched-pairs rank-biserial correlation; median difference with a
  percentile bootstrap 95% CI (10,000 resamples, seed 20261027).
- **Secondary tests:** pipeline vs expert and expert vs plain on all measures, and
  pipeline vs plain on secondary measures, Holm-corrected as a separate family.
- **Agreement (RQ3):** Spearman correlations between all measures across pieces.
- **Exploratory (RQ4):** song mode on all 48 requests with MusicGen, 3 versions each, same
  seed; version 3 vs version 1 on each measure with the same tests, clearly labelled
  exploratory.
- **Inference criteria:** a hypothesis is supported when its Holm-adjusted p < 0.05 and
  the median difference is in the expected direction. Non-significant results are reported
  in full.
- **Data exclusion:** failed generations are excluded and reported. A measure that is
  undefined by construction is excluded for that request only: dynamics accuracy for the
  4 requests with a flat target (r13, r20, r38, r44). No outlier removal.
- **Missing data:** pairs with a missing value in either condition are dropped for that
  test; the number of pairs is reported for every test.
- **Closed services:** Suno results, if run, are reported descriptively only and never
  enter confirmatory tests.

## 6. Other

- **Provenance:** every run writes a manifest (environment, package versions, model
  revisions, config hash, timings) and a `SHA256SUMS` file covering every output.
- **Openness:** code under MIT; documents and benchmark under CC BY 4.0; outputs shared
  where model licences allow.
- **Known limitations:** automatic metrics are proxies; the AI judge has its own biases;
  CLAP may under-represent non-Western music; 30 s pieces compress large-scale form; the
  parser was developed alongside the main benchmark.
- **Showcase songs (not analysed):** after each run the software also makes song-mode
  versions of the 15 held-out song descriptions (`config/showcase.yaml`) as a public
  demonstration. Parsing them uses the frozen parser and changes nothing; their audio and
  scores are never part of any test reported here.
- **Deviations:** any deviation from this plan will be listed and justified in the
  final report.
