# CLI-v1 lineage sidecar gate — retained integration result

Task `CLI-V1-LINEAGE-SIDECAR-GATE-20260917-001`, Issue #787. Immutable publication BASE `1a529d2b593eb246846cfa14f27ec7617b7fe966`; source-first freeze `e90266f9ff24c2a5f91410dd1a96bdcc0922ac0f`.

## Decision

**`PASS_CLI_V1_LINEAGE_SIDECAR_GATE_SCOPED`.**

The exact promoted `runtime/cli_v1/api.py` (Git blob `58e5489796959f120d973b595f36ed3d808533b3`) and exact promoted `runtime/core_v1/contract.py` (Git blob `a16620b65d22757ca9160d68feb1381306cc6ac3`) were executed unchanged. Only the presence of a content-bound lineage sidecar gate before exact CLI dispatch changed.

## Key discriminator

The historical HINT points to `[120,140]` at source `10/3`; current state is `20/5`, and explicit current revalidation points to `[420,280]`.

- `raw_cli / hint_laundered_current_numeric`: the program still targets historical `[120,140]` but its program source is `20/5`. Exact CLI opens a session, exact session calls exact core, and core returns `accepted=true`.
- `sidecar_gate / hint_laundered_current_numeric`: content-bound sidecar/receipt identify HISTORICAL HINT lineage; the gate returns `LINEAGE_NOT_CURRENT_ADMISSION` with `open_session_calls=0` and `session_dispatch_calls=0`.
- `sidecar_gate / hint_exact_revalidated`: a distinct CURRENT `ADMISSION_DEPENDENCY` bound to point `[420,280]` and source `20/5` passes the gate; exact CLI/session/core path remains live and core accepts.
- `sidecar_gate / stale_revalidation`: the gate does not refresh numeric source. Program source `19/5` reaches core unchanged and core returns `STALE_OBSERVATION`.
- point/source/digest/role mismatches reject before session construction.
- expired lease and missing pointer capability preserve core `LEASE_EXPIRED` / `UNSUPPORTED_CAPABILITY`; invalid request preserves CLI `INVALID_OBSERVATION_SEQ` before session construction.

Thus current CLI/core numeric freshness fields do not establish target-evidence lineage when a caller has already constructed a program. A pre-dispatch lineage gate can block historical-HINT laundering without weakening or replacing existing promoted CLI/core checks.

## Integrity

One formal invocation, 22 rows, formal reruns/replacements **0**. Frozen audit: errors `[]`. Postformal source identity exact; static tests re-pass 4/4; copied-evidence/dependency corruptions reject 4/4.

## Limits

Deterministic fake-selector/session integration only; no real backend input. Lineage receipt/sidecar schemas are authored and unauthenticated. This does not decide production ABI placement (CLI sidecar vs program-v2 vs higher-level producer API), prove semantic target identity, receipt authenticity, model benefit, latency/token savings or cross-platform live execution. Shared runtime/CLI sources are not modified by this experiment.
