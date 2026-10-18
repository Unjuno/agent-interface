# Issue #8604 T0 A01 — execution STOP

Formal candidate CLI invoked once from freeze commit `4545673dd7aabf54071056426b09d4c393a1dd92` with `python -B candidate.py --input cards.json --output raw/candidate.json`. The module printed the fixture to stdout rather than creating the requested output file. The orchestration retained a truncated stdout rendering only; exact stdout bytes and exit status are unavailable. Candidate output is absent, so the independent auditor was not invoked. No retry, repair, overwrite, or post-freeze source/input edit was made.

Disposition: `STOP_CANDIDATE_OUTPUT_CONTRACT`; no scientific result. See `REPORT.md` and `RUN.json`. Any repaired CLI requires a fresh, separately frozen successor allocation.
