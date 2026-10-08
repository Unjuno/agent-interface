# PLANNER-GAP-ENVELOPE-RUNG0-20260918-001

BASE: `e690e155aa00fb72a30586513caf9bfeec9a8a7d`
Issue: #1024
Reservation branch: `research/planner-gap-envelope-rung0-20260918-001`
Execution: disposable container only; no GUI/X11/model/provider/network/task input/shared runtime.

## H
Holding the frontier-authored envelope, state trace, allowed action vocabulary, and independent semantic oracle fixed, a local controller that re-evaluates current evidence on every planner-gap update will preserve the correct bounded disposition and YIELD on hard invalidation/currentness loss, whereas replaying the first cached action will become stale after those changes.

## T
Nine frozen trace families, 64 traces/family, four rows/trace = 2,304 rows. Every trace starts with CURRENT/LIVE/generation-1 evidence and an actionable nonzero error. Step 2 introduces exactly one family-specific mutation and step 3 retains it.

Arms:
- `CACHED_ACTION`: cache the step-0 action proposal and repeat it without current evidence re-evaluation.
- `CURRENT_ENVELOPE`: recompute from current generation, target status, evidence role, hard invalidation, action budget, error sign and allowed actions.

Families: `NONE`, `HARD_INVALID`, `GENERATION_CHANGE`, `TARGET_STALE`, `TARGET_MISSING`, `HISTORICAL_EVIDENCE`, `ERROR_REVERSAL`, `ZERO_ERROR`, `BUDGET_EXHAUSTED`.

Independent oracle is separately implemented. No state mutation depends on either arm. No output grants authority or task input.

## D
`PASS_PLANNER_GAP_ENVELOPE_RUNG0_SCOPED` only if:
1. `CURRENT_ENVELOPE` equals the independent oracle on all 2,304 rows.
2. Candidate emits zero `ADVANCE` proposals where oracle requires `YIELD`.
3. Candidate emits no authority/task-input/admission grant on any row.
4. `CACHED_ACTION` matches oracle on all 256 `NONE` rows.
5. `CACHED_ACTION` mismatches oracle on every post-mutation row (steps 2-3) in all eight mutation families: 1,024/1,024 discriminator rows.
6. Malformed/unsupported controls fail closed.
7. Frozen source/result/audit hashes match; formal invocation=1, reruns=0.

Any candidate action on hard-invalid/stale/missing/historical/generation-mismatch/budget-exhausted evidence is `FAIL_ENVELOPE_ESCAPE`. Any candidate/oracle mismatch is `FAIL_RUNG0_SEMANTICS`. If cached replay does not expose the preregistered discriminator, retain `HOLD_NO_RUNG0_DISCRIMINATOR`.

## C / U
The fixture is authored and deliberately makes a cached action stale after one explicit state mutation. A PASS proves current-evidence/envelope semantics only; it does not show that a learned backend is necessary, nor any real planner-wait, application-effect, token, MAP01, live-authority or cross-domain benefit. Rung1 requires a separate allocation.

## Roadmap
reservation/claim -> excluded toy construction -> freeze source/schedule/auditor -> publish/read back freeze -> mandatory ownership reread -> one deterministic formal invocation -> independent audit/corruption/source rehash -> retain first outcome -> stop before Rung1/model/GUI.
