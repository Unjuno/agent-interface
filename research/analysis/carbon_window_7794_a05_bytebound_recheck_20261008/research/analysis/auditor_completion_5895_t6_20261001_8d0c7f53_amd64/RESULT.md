# T6 formal result — scoped synthetic CLI experiment

## Outcome

`METHOD_REPRODUCED_SCOPED`. The candidate ran once in a network-disabled Linux/amd64 OrbStack container (exit 0); the eight observed target exits exactly matched preregistration `[0,0,0,1,1,1,1,0]`. A separate raw-only auditor ran once in its own network-disabled Linux/amd64 container (exit 0): `PASS_INDEPENDENT_RAW_AUDIT`, eight cases, no errors. No retry.

| Case | Mutation | Expected/actual target exit | Finding |
|---|---|---:|---|
| control | integer `0` | 0 / 0 | control accepted |
| bool_false | Boolean `false` | 0 / 0 | false incorrectly accepted as successful completion |
| float_zero | float `0.0` | 0 / 0 | float zero incorrectly accepted |
| null | null | 1 / 1 | rejected |
| string_zero | string `"0"` | 1 / 1 | rejected |
| missing_code | no exit code | 1 / 1 | rejected |
| duplicate_success | duplicate success completion | 1 / 1 | rejected |
| success_plus_failure | one exit-0 and one exit-1 completion | 0 / 0 | mixed completion set incorrectly accepted |

Candidate manifest, per-case raw JSONL/audit JSON/stdout/stderr, independent-audit transcript, Docker CIDs, image inspections, running-container snapshots, exits, and full container inspect JSON are retained under this package's `results/formal-t6-01/`. Candidate output and host receipts are separated. Candidate and auditor each used the frozen source read-only; the auditor mounted candidate output read-only.

## Execution identity

- Allocation: `AUDIT-COMPLETION-5895-T6-AMD64-20261001-01-8d0c7f53`; owner thread `01a0b98b-8d0c-7f53-92bc-4c6a28d73c73`.
- Main freeze / branch base: `722c42bf0d6d808cf80575ecb6353401de934b26`.
- Start gate: 2026-10-01 12:38:00 UTC. Candidate container created 12:38:19.320532937Z; auditor container created 2026-10-01T12:38:34.378431423Z (exact nanoseconds in inspect JSON). Slot released 12:38:45 UTC.
- Context `orbstack`; host macOS ARM64; guest `linux/amd64`.
- Image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, platform image ID `sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`.
- PR #5630 target head `288d0498d11cf16657e523a04616bf4f49cd94f4`; exact target blobs and source SHA-256 values are in `FREEZE.json` and candidate manifest.
- Candidate container `8e77d2f64173d13df13018dfd6fc5c33d666a36eb4b82b0ec60049e7c90c917d`; auditor container ID is retained in `results/formal-t6-01-host/auditor.cid`.
- Both containers: 1 CPU, 512 MiB, 64 PIDs, network none, read-only root, no-new-privileges, all capabilities dropped; no model/GPU/GUI/X11/input/task-effect authority.

## H / T / D / C / U

**H:** the frozen synthetic CLI auditor selects `runner_complete` rows by `exit_code == 0` before validating completion cardinality, thereby treating Boolean `false` and float `0.0` as integer zero and ignoring a failing completion row when one success exists.

**T:** one frozen eight-case candidate in a bounded pinned Linux/amd64 container and, after candidate exit 0, one separate bounded raw-only auditor container. No retries.

**D:** exact exit vector `[0,0,0,1,1,1,1,0]`, all artifacts/hash bindings valid, independent auditor PASS with no errors.

**C:** only the synthetic JSONL command-line auditor boundary at PR #5630's frozen source. This establishes reproducibility of the defect on the specified CPython/Linux/amd64 image, not production behavior.

**U:** no formal X11 provenance, physical key-up timing, keymap, MAP01 occupancy, safety/efficacy, latency, model/provider, GPU, GUI, or Issue #59 completion claim.

## Integration

T5 remains the separate pre-candidate `STOP_PREREG_PLATFORM_SCOPE_MISMATCH`; its unchanged source comment is linked from `PREDECESSORS.md`, with a whitespace-normalized transcription at `predecessors/T5-STOP.md`. Neither that STOP nor earlier T3/T4 attempts were edited or reused. Local CI, artifact hashes, analysis index, and workspace index are recorded in `CI.md`. GitHub Issue #5895 and queue Issue #5085 contain the result and early slot release.
