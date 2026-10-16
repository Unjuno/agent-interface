# T0-01 execution record

- Allocation: `MAP01-OWNER-KEYUP-BRACKET-HOST-CONSTRUCTION-5156-T4-20261002-01`
- Frozen main: `97afcb82f90616589801a256893f886010ed6d27`
- Candidate command, invoked once: `python -B run_candidate.py --out results/host-t0-01/raw.jsonl`
- Candidate process output: `{"candidate": "SYNTHETIC_HOST_OWNER_BRACKET", "owner_stopped": true, "release_requests": 1, "rows": 6, "sync_returns": 1}`
- Candidate exit code: `0`
- Auditor command, invoked once after candidate exit 0: `python -B audit_raw.py results/host-t0-01/raw.jsonl results/host-t0-01/audit.json`
- Auditor process output: `{"decision": "PASS_SYNTHETIC_OWNER_BRACKET_JOIN_SCOPED", "errors": [], "ordering": "caller_start <= owner_release_request <= owner_sync_return <= caller_return", "release_occurrences": 1, "rows": 6, "scope": "fake-Xlib host construction only; no physical X11 or application effect"}`
- Auditor exit code: `0`
- Pre-candidate construction test command: `python -B -m unittest -v test_audit.py` — 8 tests passed.
- Pre-candidate syntax command: `python -B -m py_compile run_candidate.py audit_raw.py test_audit.py` — exit code 0.
- After fast-forwarding the integration branch to current main `4cf0a3dfde1219671b671bf0a9079a11dcb2e159`, the same unit suite was rerun (8/8 PASS), syntax compilation (exit 0), and `git diff --check` (exit 0). Both frozen owner source blobs were unchanged; candidate invocations during this verification: 0; raw-auditor invocations: 0.
- Retry/substitution count: `0`.
- Candidate raw SHA-256: `10819f614b691a692e2df23a93a125a693433dc94198e575b4dc01c208f04e26`.
- Independent audit SHA-256: `4ec01ae6dd1f46cb105380324f0a50d1b3fa19eac0e5d0e08a77ccb863a8000d`.
- Frozen plan/source/package identity manifest SHA-256: `a9cf4bc41d2f58866096433c4adf5e43960342d994984d88515f2f5de0912b98` (`../../FREEZE.json`).
- Scope: Windows host CPython 3.12.10; fake Xlib backend; no Docker/container, real X11, GUI, game, model/provider, GPU, or physical input.

The complete raw and audit files are preserved byte-for-byte. No candidate or audit rerun is authorized by this record.
