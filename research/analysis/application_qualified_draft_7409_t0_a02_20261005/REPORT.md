# Issue #7409 T0 A02 result

## Result

The frozen raw-only auditor reports **`METHOD_PASS_SCOPED`**: it reconstructed all 8 fixture rows exactly and rejected all 8 frozen mutations. Candidate and auditor each ran once, both exited 0, and neither was retried. The candidate raw output includes the exact draft-base and observed-live revision values, token validity, derived `MATCH`/`CHANGED`/`UNKNOWN` state, and event ordering. The auditor derives those values from the frozen case inputs and compares the complete raw record; it does not trust a candidate self-report alone.

| Fixture | Staged result | Revision evidence | Effect |
|---|---|---|---|
| C1 disjoint writes, `r0→r1` | `PROMOTED` | `CHANGED`, compare at event 5 before promotion at 7 | Both human and agent fields survive |
| C2 same-field writes, `r0→r1` | `CONFLICT_HOLD` | `CHANGED` | Human title remains; agent title held |
| C3 hidden read/write dependency, `r0→r1` | `CONFLICT_HOLD` | `CHANGED` | Formula edit held after its source changes |
| C4 disjoint writes, `r0→r2` | `PROMOTED` | `CHANGED`, compare before promotion | Both edits survive on the later live revision |
| C5 separate UI context, shared backend | `REFUSED_ELIGIBILITY` | No draft/revision gate attempted | Refused before draft creation |
| C6 external side effect | `REFUSED_ELIGIBILITY` | No draft/revision gate attempted | Staged external-effect list empty |
| C7 unchanged `r0` | `PROMOTED` | `MATCH`, compare before promotion | Explicit promotion recorded |
| C8 unavailable live token | `HOLD_REVISION_UNKNOWN` | `UNKNOWN` | No promotion |

All eight mutations were rejected: missing revision receipt; current token laundered as base; base token laundered; forged changed-revision flag; comparison moved after promotion; same-field conflict promoted; hidden dependency promoted; and unknown revision promoted. The exact per-mutation outcomes are in [`results/a02/audit.json`](results/a02/audit.json).

The direct shared-live comparator remains a fixture comparator and can overwrite a human value in conflict cases; the staged path demonstrates the explicit hold. C6’s direct comparator includes its stipulated notification effect, while the staged path refuses eligibility before draft creation. These are authored values and code paths, not observed real-application effects.

## Execution and provenance

- Issue: https://github.com/Unjuno/agent-interface/issues/7409
- A01 predecessor: qualification retained in PR #8148, merged as main commit `82b6eaa0d96f233a2f3e2372adf53032dfdaab20`. A02 is a new allocation and did not rerun or alter A01.
- Allocation: `APPLICATION-QUALIFIED-DRAFT-7409-T0-A02-20261005-01`.
- Frozen base main: `82b6eaa0d96f233a2f3e2372adf53032dfdaab20`; freeze commit: `ab7dcd4a7baec266d7d467e9cd9be5e645c70203`.
- Issue preregistration: https://github.com/Unjuno/agent-interface/issues/7409#issuecomment-5992188208.
- Image: `python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c`, Linux arm64. Docker client 29.5.2; server 29.4.0.
- Runtime requested network disabled, one CPU, read-only root and source, separate writable output, and 16 MiB noexec/nosuid tmpfs. CPU/cgroup enforcement was not independently verified; swap was not assessed. Docker warned that `DOCKER_INSECURE_NO_IPTABLES_RAW` is set.
- The separate mount preflight passed source read, source-write rejection, and output write/readback.
- Raw candidate SHA-256: recorded in `results/a02/SHA256SUMS`; auditor record and all stdout/stderr/exit receipts are also hashed there. `results/a02/run_metadata.json` records exact invocation budgets, commands, hashes, and post-run container state.

The candidate sees only the frozen cases. The auditor consumes frozen cases and candidate raw JSON without importing the candidate. Both implementations and the finite oracle cases were authored by the same worker, so this is not independent human review.

## Scope and next gate

This supports only the listed deterministic fixture outcomes. The result does not validate application-native draft isolation, revision token authenticity/monotonicity, server-side atomic compare-and-promote, formula or dependency completeness, browser behavior, focus/live-view interference, concurrent human behavior, user benefit, or safety. The higher-level T1 hypothesis remains **not evaluated**. A real-app experiment needs a separately governed allocation with actual application revision semantics and independently controlled edits.
