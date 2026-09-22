# Transactional text group v1 — Issue #16 finite correctness rung

## Decision

`PASS_TRANSACTIONAL_GROUP_COMPENSATION_BOUNDARY_SCOPED`

This is a live GUI correctness/mechanism rung for Issue #16. It is not a production ActionGroup ABI, a same-model benefit study, or evidence of generic GUI transactions.

## H

A bounded two-step GUI group can distinguish `COMMITTED`, `ABORTED_NO_EFFECT`, `ABORTED_COMPENSATED`, and `ABORTED_PARTIAL` when compensation is separately admitted against current application history. Blind Undo after an intervening edit can restore the primary text while deleting unrelated external input and falsely report compensation.

## T

Actual environment: provided Linux x86_64 execution container, CPython 3.13.5, Tcl/Tk 8.6.16, Python-Xlib 0.15, allocation-owned authenticated Xvfb with TCP disabled. Docker/Podman CLI were unavailable, so this is not Docker/OrbStack image-attested replication. No model/provider, network experiment, host desktop, user data, install, or shared runtime mutation.

Three policies:
- `STEPWISE_BASELINE`: stop after a failed partial action; no automatic compensation.
- `GROUP_BLIND_COMPENSATION`: issue ordinary Undo after a partial effect and call it compensated if only the primary text returns to the initial value.
- `GROUP_REVISION_BOUND`: issue Undo only if the current text/revision still matches the post-step1 receipt; otherwise return unresolved partial state.

Five schedules:
- `SUCCESS`
- `FAIL_BEFORE_EFFECT`
- `FAIL_AFTER_STEP1`
- `FAIL_AFTER_STEP1_WITH_INTERVENING_EDIT`
- `COMPENSATION_UNAVAILABLE`

Three repetitions per cell = 45 fresh Tk application processes in three immutable 15-case batches. Formal retries/replacements/post-freeze source tuning: 0.

Task and external edits use real XTEST keyboard input. The application IPC is read-only snapshot/close. F11 is an explicit fixture history-reset control, not a generic GUI cancellation primitive.

## D / first formal outcome

All three formal batches completed with external exit 0 and empty stderr. Separate raw-only audit passes 15/15 in every batch with `errors=[]`. Eleven copied-evidence corruption controls per batch reject, including ten manifest-rehashed semantic/provenance mutations plus a source-hash mutation. All six frozen source/plan/environment SHA-256 identities remained unchanged.

Aggregate candidate outcomes:

| Candidate outcome | Count |
|---|---:|
| COMMITTED | 9 |
| ABORTED_NO_EFFECT | 9 |
| ABORTED_COMPENSATED | 9 |
| ABORTED_PARTIAL | 18 |

Independent audited outcomes: 42 `PASS`, 3 `FAIL_WRONG_COMPENSATION_COLLATERAL`.

Key cells across three repetitions:

| Condition | Stepwise | Blind group | Revision-bound group |
|---|---|---|---|
| SUCCESS | COMMITTED 3/3 | COMMITTED 3/3 | COMMITTED 3/3 |
| FAIL_BEFORE_EFFECT | ABORTED_NO_EFFECT 3/3 | ABORTED_NO_EFFECT 3/3 | ABORTED_NO_EFFECT 3/3 |
| FAIL_AFTER_STEP1 | ABORTED_PARTIAL 3/3 | ABORTED_COMPENSATED 3/3 | ABORTED_COMPENSATED 3/3 |
| INTERVENING_EDIT | ABORTED_PARTIAL 3/3 | **reported ABORTED_COMPENSATED but audited FAIL 3/3** | ABORTED_PARTIAL/refused 3/3 |
| COMPENSATION_UNAVAILABLE | ABORTED_PARTIAL 3/3 | ABORTED_PARTIAL 3/3 | ABORTED_PARTIAL 3/3 |

In every blind intervening-edit case, raw application history records `base:p -> base:px -> base:pxy -> base:p`: the task `x` effect and unrelated external `y` were in the same current Undo group, and blind Undo erased both. Primary text restoration alone therefore produced a false compensation claim. The revision-bound policy observed the changed revision, sent no Undo, preserved `base:pxy`, and returned unresolved `ABORTED_PARTIAL`.

Successful compensation after an uncontested step1 remains historically distinct from no-effect: the raw journal records the `x` effect before Undo, and the result retains `task_effect_occurred=true`.

All 45 applications exited 0 and all 45 final X-server key/button observations were neutral. X-server state is not physical HID telemetry.

## Construction / retained failures

Construction is excluded from formal evidence. Four pre-freeze failures are retained as engineering evidence:
1. controller Xauthority was not visible to python-Xlib readiness checks;
2. Tk internal focus existed but the X server input focus was not set;
3. the fixture blocked on stdin instead of running the Tk event loop;
4. an audit local variable shadowed the semantic `expected(...)` function.

After correction and before freeze, excluded construction passed 5/5 with raw audit errors=[] and 10/10 rehashed semantic corruption controls rejected. None of those rows were pooled into the 45 formal cases.

## C

The revision receipt and compensation semantics are authored by one cooperative Tk fixture. The blind policy is a deliberate unsafe comparator. The revision-bound policy can conservatively refuse work but cannot recover every partial state. This study does not prove that arbitrary applications expose a trustworthy revision or isolated compensation operation.

## U / integration handoff

Unresolved: same-model task quality, actual model boundaries/tokens, end-to-end latency, held-out applications, hidden history mutations, crash/power-loss atomicity, irreversible external effects, authentication, cross-platform behavior, natural failure probability, and production integration.

Issue #16 remains open. The concrete integration constraint is: `ABORTED_COMPENSATED` requires evidence for every declared preserved invariant and a current compensation scope; restoring only the primary field is insufficient. A refusal remains `ABORTED_PARTIAL`, not success.
