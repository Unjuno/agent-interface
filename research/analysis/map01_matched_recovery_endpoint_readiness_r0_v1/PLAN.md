# MAP01 matched-recovery endpoint readiness R0 — Issue #1866

Task: `MAP01-MATCHED-RECOVERY-ENDPOINT-READINESS-R0-20260919-001`
Base: `7eaa6f5ffdf710e729db0abe00a3dfa617979309`

## Purpose

Define a fail-closed entry gate for a future matched MAP01 recovery-efficacy allocation. This task does not measure recovery efficacy and does not consume a live/model/GUI/X11/ViZDoom allocation.

## Frozen gate planes

1. **physical_occupancy** — live/retained physical occupancy evidence must be lineage-bound, on comparable timing provenance, and precise enough for the declared matched metric.
2. **task_effect** — independently scored TASK_EFFECT must be plan/actuation-bound, causally attributed by the evidence contract, on a comparable clock, and support explicit unresolved/no-effect.
3. **matched_arms** — recovery/control arm contract must be matched and differ only in the intended recovery factor.
4. **audit_binding** — every pair-level decision input must be reconstructed or exactly bound to arm evidence by an independent fail-closed audit.
5. **terminal_release_independence** — release/terminal/integrity evidence must remain independent from task-effect semantics and grant no semantic/input authority.

Only all five retained-ready planes may authorize a future allocation.

## Evidence snapshot intent

The current BASE is expected to HOLD because:
- retained MAP01 occupancy is `SCHEMA_CENSORING_TOO_WIDE`;
- retained v39 timing endpoints are blocked and lack `first_useful_effect`/clock provenance;
- #1838 proves old state feedback/viewport/terminal evidence cannot identify useful occupied control without both causal binding and comparable effect timestamp;
- #1839 is open with construction-only evidence and formal0 at snapshot;
- #1609 confirmed a v6 pair-summary/arm binding gap;
- #1632 is open and has not yet retained its repair result at snapshot.

The v6 prereg already supplies a matched three-pair arm definition, and #1609's retained negative controls show that arm invalidity/wrong planner boundary still fail closed. These are treated as contract readiness only, not live efficacy.

## Formal

One source-frozen deterministic invocation:
- evaluate the frozen current snapshot;
- exhaustively enumerate all 32 ready/not-ready vectors over the five gate planes using fully valid canonical gate records;
- require exactly one AUTHORIZE row: all five ready;
- run fixed evidence-laundering controls for viewport/HUD/terminal/run-score substitution, open-prerequisite promotion, and unbound pair-summary promotion.

Independent audit re-derives all decisions without importing candidate helpers.

## Stop

Retain first PASS/HOLD-gate result and audit. No live successor is authorized by a HOLD. Active prerequisite closure later requires a fresh successor; this snapshot is not rewritten.
