#!/usr/bin/env python3
# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""One entry point for everything. Examples:

    python run_all.py check                      # what is installed, which keys are set
    python run_all.py quick                      # few-minute smoke test
    python run_all.py full                       # the preregistered study
    python run_all.py song --request "..." --lyrics lyrics/my_song.txt
    python run_all.py verify results/<run-id>    # check every SHA-256 hash
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from orchestra.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(root=ROOT))
