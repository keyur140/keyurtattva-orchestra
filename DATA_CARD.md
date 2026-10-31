# Data card: Orchestral Input Pipeline benchmark and outputs

**Author:** KEYUR SHAILESHKUMAR PATEL, ORCID https://orcid.org/0009-0008-5261-043X
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science,
Brunel University London, UK; (2) Independent researcher.
*Conducted independently; not an official Brunel University London project.*

**AI assistance statement:** This project was developed by KEYUR SHAILESHKUMAR PATEL with the help of an AI assistant (Claude, by Anthropic) for drafting text, writing and testing code, and literature search. All research decisions, the study design and the final content were chosen and approved by the author, who takes full responsibility for the work.
**Licence:** requests and targets CC BY 4.0; generated music CC BY-NC 4.0 with the credit "Music by KeyurTattva (KEYUR SHAILESHKUMAR PATEL)" (see `LICENSE-DOCS.md`)

## What is in it

| Part | File | Description |
| --- | --- | --- |
| Benchmark requests | `config/requests.yaml` | 48 free-text requests for orchestral and cross-cultural pieces, each with author-written targets: instrument families, form, dynamic shape, and (for 10 requests) a cultural style description |
| Held-out requests | `config/heldout_requests.yaml` | Requests written after the parser was frozen, for a fair parser test (to be filled in) |
| Per-run outputs | `results/<run-id>/` | Generated audio and MIDI, specifications, prompts, metric tables, hypothesis tests, reports, manifest, SHA-256 sums |
| Song outputs | `songs/<id>/` | Refined versions of one song, scores, lyrics, report, manifest, SHA-256 sums |

## Coverage

Families (number of requests): strings 35, brass 20, percussion 20, woodwinds 19,
keyboards and harp 15, voices and choir 12, Indian instruments 10, electronic and hybrid 6. Forms: overture,
sonata, theme and variations, rondo, film cue, song, march, chorale, raga performance,
through-composed. Dynamic shapes: crescendo, decrescendo, arch, terraced, flat.

## How it was made

The author wrote the requests and targets. No data were collected from people, and no
personal data are included. Generated audio comes from the models listed in each run
manifest.

## Known gaps and biases

- Requests are in English only.
- Indian styles are represented mainly by Hindustani ragas and Gujarati and Bollywood
  idioms; other traditions are not covered.
- Targets reflect one author's judgement of what a listener would expect.
- Pieces are short (30 s by default).

## Intended use

Research on controllable music generation and its evaluation. Not intended for imitating
specific artists or for commercial use of generated audio where model licences forbid it.
