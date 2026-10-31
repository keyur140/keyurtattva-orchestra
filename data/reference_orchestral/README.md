# Reference recordings for Frechet Audio Distance (FAD)

The reference set is fixed in advance in `config/fad_reference.tsv`: 52 orchestral recordings
from the MTG-Jamendo dataset (Bogdanov et al., 2019), each with its SHA-256 and its own
Creative Commons licence.

Fill this folder with:

    python run_all.py fetch-reference

It downloads two archives (about 3 GB in total), checks every SHA-256, keeps only the 52
listed tracks and writes `ATTRIBUTION.md` with each track's credit and licence.

Rules for a rigorous run:
1. Do not add or remove files after the run starts; the manifest stores the SHA-256 of
   every reference file.
2. The audio is used only to compute embeddings for a non-commercial research comparison.
   Do not redistribute it; share `config/fad_reference.tsv` instead.
