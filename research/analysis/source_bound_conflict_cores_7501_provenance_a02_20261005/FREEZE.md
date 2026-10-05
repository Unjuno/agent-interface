# A02 immutable pre-run freeze

- Issue: #7501, additive source provenance boundary; does not alter T0/A01.
- `main` at intake/freeze: `18bf390d0c230b5a2ee9675cebffbc0e51bfea2d2` (confirmed with `git ls-remote` against `refs/heads/main` immediately before the fixture was generated).
- Execution: Ubuntu WSL, CPython 3.12.3, CPU only. Docker CLI is not installed on the Windows host. WSLc is present but not used because unresolved prior WSLc processes were recorded; none were stopped or modified. This is not a Docker/WSLc comparison or a memory/resource-enforcement test.
- Formal invocation budget: generator 1 (completed before freeze); candidate 1; independent auditor 1; retries 0. Candidate/auditor invocations have not yet occurred at this freeze.
- Mutation controls are applied only in-memory by the auditor to retained input/output; candidate is not rerun.
- No model, GUI, GPU, live task, dispatch or external effect.

## Frozen files

SHA-256 (computed in Ubuntu WSL after the sole fixture generation, before candidate/auditor):

| File | SHA-256 |
|---|---|
| `README.md` | `f2ed6611c55f706db83fc61e3d1fa951959bb56e2f599193fc383b84ba64a503` |
| `generate.py` | `29ecc7f64c627d04a3e81f5e4b32c539127fb36a5b77ccf4730b729887adb2ca` |
| `candidate.py` | `048b4c676f1e44bb1b37087b79388a1a446bc6adeb36d7b5bc0fca619088125a` |
| `audit.py` | `d213b3a53b5a251fe7c5e6c1698e3ec4a777815f0b4ad9f1a53cb208142eb919` |
| `INPUT.json` | `5be1bb09bb7ad6554d830e138e46869f5acb69b0b1c88f4d53669a73567c9547` |

The generator emitted ten cases: one valid SAT, one pair conflict, one two-MUS case, three provenance faults, stale revision, missing background, hard-background conflict, and unknown clause. Python bytecode compilation passed before the formal freeze; it is not a candidate/auditor invocation.

## Decision gate

The only positive disposition is `PASS_PROVENANCE_BOUNDARY` when the independent oracle matches all ten candidate outcomes, the expected core sets and fail-closed cases are verified, dispatch/input authority stay false, and eight distinct mutation controls are rejected. Any scientific mismatch is `FAIL_METHOD`; any post-freeze execution/artifact failure is retained as `STOP_INFRA` without retry. Results are limited to this deterministic finite CPU fixture.
