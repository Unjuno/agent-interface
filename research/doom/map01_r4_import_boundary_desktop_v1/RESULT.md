# Issue #3903 — Docker Desktop static import-boundary audit

## Outcome: `PASS_STATIC_IMPORT_BOUNDARY_SCOPED`

Exactly one formal Docker container invocation completed successfully on Docker Desktop 28.5.1 (`linux/amd64`) using the cached immutable Python image recorded in `SOURCE_MANIFEST.json`. The candidate and independent verifier both classify all eight controls correctly and agree that the frozen `session_entry.py` contains an unguarded module-executed `session_map01_v13.main()` call; the correct boundary disposition is `REFUSE_UNGUARDED_MODULE_LAUNCH`.

Endpoint counts are all zero: target import 0, target execution 0, game 0, model 0, input 0, construction 0, formal 0. The target itself was parsed as source text only. It was never imported, compiled, or executed. `result.json` and `audit.json` retain the raw candidate and independent reports; `SHA256SUMS` covers both.

## Independent audit

The separate stdlib-only implementation ran in the same single container invocation. It independently reconstructed target module-call contexts and each synthetic control, returned `PASS_INDEPENDENT_AUDIT`, and matched both frozen input SHA-256 digests. The candidate returned 8/8 controls and `PASS_STATIC_IMPORT_BOUNDARY_SCOPED`.

## Construction history

Host unit tests first exposed two classifier defects (lambda body traversal and `try/finally` context); both implementations were corrected independently and the failures preserved in `CONSTRUCTION.md`. Two launcher preflights then stopped on repo-root path miscalculation before Docker ran. Those setup failures are retained; no output was overwritten, and the one formal Docker invocation later passed.

## Reproduction and integrity

- Protocol and frozen identities: `PREREG.md`, `SOURCE_MANIFEST.json`.
- Run host construction controls: `python -m unittest discover -s tests` from this directory.
- Formal Docker command: `./run_formal.ps1` from the repository root; refuses an existing output directory and any identity mismatch.
- Formal artifacts: `results/formal01/result.json`, `results/formal01/audit.json`, `results/formal01/SHA256SUMS`.
- The formal output directory is not reusable. Do not rerun this allocation.

## Limits

This is a static AST classification result only. It does not establish transitive import safety, runtime behavior, workflow policy, correctness of the historical experiment, or any gameplay/product property. It does not reinterpret or replace the prior STOP in PR #3900, and it does not close the separate OrbStack-specific question.
