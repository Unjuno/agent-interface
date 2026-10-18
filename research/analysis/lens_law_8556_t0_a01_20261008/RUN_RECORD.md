# Formal run record

- Run: `8556-t0-a01-20261008`
- Issue: #8556, Lens-law conformance for GUI observation and update adapters.
- Base commit: `6ea1269defb6d48a607f13b08f1aa2d223ba06e9`.
- Runtime: CPython 3.12.10, Windows 11 build 26200, AMD64. This is a host-run pure finite-model study, not a container run.
- Frozen source/input/protocol digests: see `FREEZE.json`; frozen files were not modified after formal execution.
- Construction tests: `python -B -m unittest -v test_candidate.py test_audit.py` — 16 tests passed before freeze.
- Candidate invocation: once; exit 0; 12 fixture rows. Output: `results/candidate.json`.
- Independent auditor invocation: once; exit 0; `PASS_LENS_LAW_METHOD_SCOPED`; rows 12; fixture SHA-256 `4a45a620ee0e7d79f0fe4805f5b25aba8926d80a003e45c504b924417289f88d`; mutation controls rejected 4/4. Output: `results/audit.json`.
- Findings: wrong-field and ignored updates violate Put–Get; duplicate callback violates scoped Get–Put (and Put–Put) despite final label match; first-write-wins violates Put–Put although its single-write final label matches. Final-label-only misses both latter cases; same-request replay is true on all enumerated cases and misses the seeded failures.
- Abstention: ambiguous applicability and stale/pending states are UNKNOWN; partial and non-idempotent operations are NOT_APPLICABLE. No abstention control returned PASS.
- Scope/limitations: authored finite fixtures only; no GUI/application route was exercised. No Docker, WSLc, native WSL, network, external service, or user data was used. No portability or real-route claim.
- Stop reason: predefined one candidate + one auditor run completed; no retry permitted or needed.
