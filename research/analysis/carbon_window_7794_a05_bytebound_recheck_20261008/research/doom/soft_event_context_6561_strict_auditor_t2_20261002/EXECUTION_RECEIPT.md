# Execution receipt — SOFT-EVENT-AUDITOR-STRICT-T2-20261002-01

- Frozen current-main at candidate start: `ce89f11fcff33b83de4a9b9ded7b89bf764b5f09`. Main later advanced through unrelated research-preservation merges; their commit diffs did not modify the frozen guard implementation. The PR branch is based on current main `18115cdfb209222c3304fe3624edd8a962512194`. Frozen guard implementation SHA-256: `7BE055C4BD68A1528F4B2B02B543435BD64465EA42D4452F5597D6DCE08442A0`.
- Pre-run `git ls-remote` agreed with the freeze; all 12 entries in `PRE_RUN_SHA256SUMS` matched; output path was absent.
- Preparation: `python -B -m unittest -v test_t2.py` — 6/6 passed before the formal candidate.
- Candidate: `python -B run_candidate.py results/t2-20261002-01` — invoked once, exit 0, `PASS_T2_STRICT_AUDITOR_SCOPED`; 1 control accepted, 5/5 mutations rejected. Candidate output timestamp: `2026-10-02T07:08:41Z`.
- Independent audit: `python -B audit_t2.py results/t2-20261002-01` — separate process, invoked once after candidate exit 0, exit 0, `PASS_INDEPENDENT_RAW_AUDIT`, errors=0. Audit output timestamp: `2026-10-02T07:08:47Z`.
- Runtime: Windows 10 build 26200, CPython 3.11.9 x64, host CPU. Candidate/auditor did not call network or use WSLc/container, Docker, GPU/CUDA, model, GUI, game, or user input.
- Candidate=1; separate auditor=1; retries=0. No result files from T1 were modified; no T1 generator or target auditor was rerun.
- Output hashes: see `EVIDENCE_SHA256SUMS`.

