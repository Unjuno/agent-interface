# One-shot run log

- Allocation: `REACHABLE-TUBE-6089-T0-HOSTCPU-20261002-01`.
- Frozen main: `702c411c54af2e83b7b5b9640a0ace26be973b45`.
- Branch source commit before formal run: `7f6254608a4876e22e5e7cb689d3662949d40ebd`.
- Runtime: local Windows host, CPython 3.11.9, stdlib only.
- Pre-start: main and branch refs matched the freeze; all source SHA-256 values matched `FREEZE.json`; `candidate_raw.json` and `audit.json` were absent; observed aggregate CPU load 19%.
- Construction command: `python -m unittest -v test_method.py` — 3/3 passed (`test_corruptions_rejected`, `test_fixture_discriminators`, `test_independent_recursive_oracle_accepts_candidate`). Elapsed 0.046 s.
- Candidate: one invocation, `python run_candidate.py candidate_raw.json`; exit 0. Candidate output file creation observed at 2026-10-02 08:10:00 UTC. No replacement or retry.
- Auditor: one separate process, `python run_audit.py candidate_raw.json audit.json`; exit 0. Audit output creation observed at 2026-10-02 08:10:07 UTC; status `PASS_METHOD_SCOPED`, errors `[]`.
- Post-run raw summary: 8 cases; selected robust horizons `[4,2,5,0,2,0,0,2]`; nominal horizons `[5,5,5,1,5,0,0,5]`; invalidated-target result yielded; out-of-envelope stress marked uncertified and crossed the forbidden boundary.
- Raw SHA-256: candidate `9c7763a896e6e92bb776eabd0d3cc67e1620fb0572db10b19312bf69648833ff`; audit `5dc0bdd0180b721caf9d3cbbea8254fef6ac3d0c361d1178dc2e2bfa227fbf96`.
- Post-run observed CPU load 15%. The first post-run GitHub ref check observed main at `a80fa420dd60da7caf90165263acf736801947a1`; exact timing of that main advance relative to the candidate/audit finish was not captured. The recorded immediate pre-start check had matched the frozen `702c…` main and branch source commit.
- Resource accounting: candidate/auditor 1/1, retries 0; GPU/CUDA/model/container/network/GUI/input 0.
- Evidence delivery verification: an initial `git hash-object` check used Windows autocrlf filtering and gave misleading blob-ID mismatches for the CRLF raw JSON. Rechecked the raw byte arrays from GitHub base64 against local bytes (length and every byte equal); GitHub blob IDs also match `git hash-object --no-filters`. No result file was rerun or edited.
- STOP criteria: none triggered. No result overwrite or retry occurred.
