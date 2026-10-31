# What this work could mean for you, in plain words

**Author:** KEYUR SHAILESHKUMAR PATEL · ORCID https://orcid.org/0009-0008-5261-043X
**Affiliations:** (1) MSc Artificial Intelligence student, Department of Computer Science, Brunel University London, UK; (2) Independent researcher.
*Conducted independently; not an official Brunel University London project.*

**AI assistance statement:** This project was developed by KEYUR SHAILESHKUMAR PATEL with the help of an AI assistant (Claude, by Anthropic) for drafting text, writing and testing code, and literature search. All research decisions, the study design and the final content were chosen and approved by the author, who takes full responsibility for the work.

## 1. What you built, in one paragraph

You built a tool that writes a request for music the way a composer writes a score. It decides which section of the orchestra plays when, how loud each part is, and how the piece is shaped from start to finish. Then it gives that plan to a free AI music model, or writes a MIDI score itself. It measures the result automatically, improves it over several versions, and records everything so anyone can check and repeat the work.

You can use all of it from a browser app, **KeyurTattva Orchestra Studio** (`python run_all.py app`). Each new version starts from the best one so far, and a change that makes the music score worse is undone, so your best version never gets worse. The same request and seed always give exactly the same song, and a test checks this.

## 2. Why it matters

- **For musicians and creators.** Today most people type "epic orchestral music" and get a generic sound. Your pipeline gives them control over sections, dynamics and form without needing to know AI tricks.
- **For researchers.** You are releasing an open benchmark of 48 orchestral requests with targets, plus a package that reruns the whole study with one command. Few AI music studies are this easy to check.
- **For under-represented music.** The benchmark includes ragas, Gujarati garba and Bollywood styles. Most AI music research ignores these traditions.
- **For research practice.** Preregistration, fixed seeds and SHA-256 hashes for every file are still rare in AI music papers. This is a point in your favour.

## 3. What is new

1. Treating the prompt as a score: orchestration rules, a "conductor layer" for dynamics and form, and a prompt compiler that fits each model's word limit.
2. An open, fully computational benchmark for full-ensemble control, from solo voice to orchestra with choir and Indian instruments.
3. A measured feedback loop that improves a song over several versions and reports whether it actually got better.

## 4. Are you the first in the world?

**Short honest answer: no, not the first to control AI music with structure. But your exact combination looks new, as far as a quick search shows.** Before you write "first" anywhere, do a proper literature search (Google Scholar, arXiv cs.SD and eess.AS, ISMIR proceedings 2020 to 2026).

Earlier work you must know and cite:

| Work | What it does | How yours differs |
| --- | --- | --- |
| [Text2Score](https://arxiv.org/abs/2605.13431) (Bhandari et al., May 2026) | An LLM "orchestrator" turns a prompt into a bar-by-bar plan (instruments, key, metre, harmony), then a trained model writes sheet music | The closest to your idea. Yours needs no training, drives audio models as well as MIDI, covers full orchestra with choir and Indian traditions, and adds a measured refinement loop |
| [Music ControlNet](https://arxiv.org/abs/2311.07069) (Wu et al., 2023) | Time-varying control of melody, dynamics and rhythm | Needs a specially trained model; yours works on existing models by input design |
| [JASCO](https://arxiv.org/abs/2406.10970) (Tal et al., 2024) | Text-to-music with chords, melody and drum timing controls | Trained model; no orchestration knowledge or cross-cultural benchmark |
| [Symbolic music from natural-language prompts with an LLM-enhanced dataset](https://arxiv.org/abs/2410.02084) (ISMIR 2025) | Text to symbolic music | Symbolic only; no conductor layer or audio-model conditioning |

What looks different in yours, to check against the literature:
1. **No model training.** Everything happens in the input, so it works on top of open and closed audio models.
2. **The whole ensemble in one benchmark.** Orchestra sections, choir, Indian instruments and hybrid sounds, each with written targets.
3. **A measured refinement loop.** Versions of the same piece with the same seed, each fixing the weakest measured area, with the real scores reported.
4. **Rigour.** Preregistered, fully computational, with every file hashed and the whole study rerunnable with one command.

A safe way to phrase it, once your search confirms it: *"To our knowledge, this is the first preregistered, fully reproducible study of score-structured input conditioning for full-ensemble, cross-cultural text-to-audio generation."* Being clearly different and well tested matters more to reviewers than being first.

## 5. Credit you can honestly expect as first author

| What you can publish | What it gives you | How likely |
| --- | --- | --- |
| OSF preregistration | A public, timestamped record that the study design is yours | Certain, once you submit it |
| Code and benchmark on GitHub, archived on Zenodo | A DOI people can cite; GitHub shows a "Cite this repository" button from CITATION.cff; it links to your ORCID | Certain, once you upload it |
| Preprint (for example arXiv, category cs.SD or eess.AS) | A citable paper with your name first | Likely. First-time arXiv authors may need an endorsement from an existing author in that category |
| Workshop or late-breaking paper (for example the ISMIR Late-Breaking/Demo session, the AI Music Creativity conference, or creative-AI workshops) | A peer-reviewed or lightly reviewed publication | Realistic if the study is run carefully and written clearly; not guaranteed |
| Main-track paper at a selective venue (for example ISMIR or ICASSP) | Strong recognition in the field | Possible but competitive; many good papers are rejected the first time |

**Honest expectations:**
- Most single-author papers from independent researchers get few citations in their first year, often fewer than ten. Recognition grows slowly, through people using your code and benchmark.
- For a PhD application, the main value is proof. A public preregistration, working code and a written report show that you can plan, run and report research. Supervisors take this seriously, and it can strengthen an application that has a 2:2 degree. It does not guarantee an offer, and each university has its own entry rules.
- A null result is still a result. If the pipeline does not beat plain prompts on some measures, reporting that honestly is publishable and still counts in your favour.
- Do not describe any result before the full run is finished. The quick test is only a check that the software works.

## 6. What this work does not claim

- It does not create a new AI music model.
- It does not show that AI matches human orchestrators or composers.
- Automatic measures and the AI judge only approximate what listeners hear.

## 7. Copyright, credit and royalties for KeyurTattva

*This is general information, not legal advice. Laws are changing; check before you sell anything.*

**What the package does for you**
- Every WAV and MIDI file it makes carries "(c) year KEYUR SHAILESHKUMAR PATEL (KeyurTattva)", the licence and the required credit inside the file itself.
- Every output folder gets an `OUTPUT_LICENSE.md` that states the licence and the required credit: "Music by KeyurTattva (KEYUR SHAILESHKUMAR PATEL)".
- The SHA-256 hashes and manifests are a dated record that you made these files, and proof they have not been changed. This is useful evidence if anyone disputes authorship.
- The licence is set once in `config/study.yaml` under `output_rights`.

**What is clearly yours**
- Your code, documents and benchmark.
- Your own lyrics, your requests and the plans your pipeline writes.
- MIDI scores written by your own rule-based composer. This is your strongest claim, because no outside AI model wrote them.
- Tunes you sing or hum into a voice note. The song folder keeps your recording, its SHA-256 and a `your_tune.mid`, so the melody is clearly yours, which strengthens your claim on the whole song.

**AI-generated audio is less certain, and it depends on the country**
- **UK:** section 9(3) of the Copyright, Designs and Patents Act protects "computer-generated" works for 50 years. The author is the person who made the arrangements for the work to be created. The government [consulted on removing this rule](https://legalblogs.wolterskluwer.com/copyright-blog/copyright-and-ai-policy-in-the-uk-in-2025/) (consultation closed 25 February 2025), so check whether it still applies when you publish.
- **USA:** the Copyright Office and the courts require a human author. Prompts alone are usually not enough, but your human contributions are protected, such as lyrics, selection, arrangement and editing.
- **India:** for computer-generated works, the author is the person who causes the work to be created.

**The models' own terms also apply.** MusicGen weights are for non-commercial use. Stable Audio Open has its own community licence. Suno's terms depend on your plan: free-plan songs have been owned by Suno, while paid plans have given ownership to the user. Check the current terms. No licence of yours can override these.

**Your chosen licence: CC BY-NC 4.0.** Anyone may use, share and remix your generated music for non-commercial purposes, as long as they credit "Music by KeyurTattva (KEYUR SHAILESHKUMAR PATEL)". Companies or anyone earning money from it must get a paid licence from you, and that is where royalties and fees come from. It also fits MusicGen's non-commercial terms. One honest catch: if a piece has no copyright in a country (for example pure AI audio in the USA), a licence there may be hard to enforce. Your lyrics, your MIDI scores and your edits are what make your claim strong.

**The other options, for comparison.** The licence decides what others may do. With CC BY 4.0, anyone may use, change and even sell the music, but they must credit KeyurTattva, and no royalties are due. With CC BY-NC 4.0, anyone may use it for non-commercial purposes with credit, and businesses need a paid licence from you, which is where royalties come from. "All rights reserved" means nobody may reuse it without your permission.

**Earning royalties**
1. Register your songs with a collecting society. In the UK, PRS for Music covers the song and lyrics, and PPL covers the recording.
2. Release through a distributor, such as DistroKid, under the artist name KeyurTattva.
3. Many platforms and societies now ask whether AI was used, and some refuse fully AI-generated works. Always disclose AI use honestly. Works with strong human input (your lyrics, melodies and edits) have the safest claim.

**Avoiding problems later**
- Never imitate a named artist's voice or song.
- Use the same name everywhere: KeyurTattva on platforms, and your full name with ORCID on research.
- Keep every manifest and `SHA256SUMS` file.
- Get advice from a music lawyer before selling licences. The UK Intellectual Property Office and the Musicians' Union have free guidance.

## 8. Two modes: explore, or make and publish as Tattva

Every song is made with `--purpose explore` (the default) or `--purpose publish`.

| | Explore | Tattva publish |
| --- | --- | --- |
| What it is for | Trying ideas and research | Music you will release as KeyurTattva |
| Models allowed | All, including research-only MusicGen | Only routes whose terms let you own and release the result: MIDI route (your own composer), Suno on a paid plan, Stable Audio Open under its Community License |
| What you must confirm | Nothing | For Suno or Stable Audio, a yes in `.env` (`SUNO_PAID_PLAN`, `STABLE_AUDIO_LICENCE_ACCEPTED`), recorded in the manifest |
| Mark inside each file | "Exploration output - not cleared for release" | "Tattva publish mode", with the reason it is cleared |
| Extra files | None | `RELEASE_CHECKLIST.md`, `AI_DISCLOSURE.txt`, `HUMAN_CONTRIBUTIONS.md` |

Publish mode uses the same improvement loop and the same measures as explore mode, so the
quality does not drop. It also adds an honest sound-quality check to the release checklist.
For example, if the MIDI route used the built-in demo synthesiser, the checklist tells you to
render it with a good orchestral soundfont, or to load the MIDI file into a music program with
professional orchestral instruments, before release.

For the most professional sound you can own: use the MIDI route and render the MIDI with
professional orchestral sample libraries, or use Suno on a paid plan for sung songs. Then add
your own mixing, edits or re-recorded parts and write them in `HUMAN_CONTRIBUTIONS.md`. Human
work is the strongest part of a copyright claim. Publish mode is a safety net, not legal advice.

## 9. Ownership and licences

- You release the code under MIT and the documents and benchmark under CC BY 4.0. Anyone may reuse them, but MIT requires them to keep your copyright line, and CC BY requires credit.
- You chose the free, open route with no patent. Your copyright stays yours, and the dated public release (OSF and a Zenodo DOI) proves you did it first, which stops anyone else patenting the same idea.
- Audio made with MusicGen, Stable Audio Open or Suno is also bound by those models' own terms, and some of them forbid commercial use. Check each model card before you release or sell audio.
- This work was done independently. Check Brunel University London's regulations on student intellectual property if you used any university resources.

## 10. Steps to get the credit

1. Write the held-out requests, then register the preregistration on OSF.
2. Run `python run_all.py full` and keep the results folder exactly as written. `SHA256SUMS` proves it was not changed.
3. Put the code and results on GitHub, then archive a release on Zenodo to get a DOI.
4. Write the paper, post a preprint, and submit it to a workshop or conference.
5. Add every output to your ORCID record.
