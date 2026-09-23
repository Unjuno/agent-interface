# Finite actual-X11 pointer wake comparison

Six scripted Inkscape arms compared executor_v4/lease_cause_v1 (old) against
executor_v5/lease_cause_v2 (new). Both used cause_session_v1 and input_owner_v10.
The plan, source hashes, identical within-pair program, seed, five-second lease,
and physical-button-triggered focus injection were saved before execution. Orders
were old/new for interrupted click, new/old for interrupted drag, and old/new for
normal drag. All three pairs had identical initial PNG hashes. No arms were rerun.

| Condition | Old status | New status | Old release→terminal | New release→terminal |
|---|---|---|---:|---:|
| Interrupted 250 ms click | completed, 1 step | needs_decision, 0 steps | 341.319631 ms | 1.605554 ms |
| Interrupted 1000 ms drag | needs_decision, 0 steps | needs_decision, 0 steps | 997.300850 ms | 0.865724 ms |
| Normal 1000 ms drag | completed, 1 step | completed, 1 step | not applicable | not applicable |

The old click actually returned completed with a verified focus_changed cause;
this is now reproduced on a real application, beyond the earlier inference and
synthetic presentation test. The new candidate returned a decision with zero
completed steps. Both interrupted drags admitted only the starting motion, not
the tail motion. All interrupted arms physically released Button1 after transfer;
all six arms had the button up and verified owner release at terminal.

These observations support the mechanism: cooperative wake removes a residual
scheduled pointer wait in these cases. One pair per condition cannot establish a
latency distribution, population effect, p95, or hard real-time bound. Orders are
specified but not a randomized large study. No model or socket was in this timing
path; it measures the runtime executor/backend directly. It is not a human-speed
comparison or end-to-end task improvement claim.

## Semantic limitation discovered during review

Both normal drag arms admitted the two intended motions and completed without an
interruption. However, the assistant's inspection of the new arm's final image
did not show the rectangle moved or selected. The test did not save or independently
score the document. Its normal-control success therefore means input sequence and
release completion only, **not a successful application drag task**. Preserve this
observation; do not promote the normal-control checks into a task-success metric.

Next use an explicitly selected object, a new drag case, save, and an independent
document oracle. Compare old/new task accuracy and recovery as well as runtime
notification. Also retain the fast-terminal/no-image behavior from cause-live-02;
urgent notification and a useful recovery image are separate delivery needs.

## Evidence

`pointer_wake_comparison_v1.py` and `results/pointer-wake-comparison-01/` retain the
pre-execution plan, all six arm reports including owner records, injection checks,
frames, setup diagnostics, and cleanup return status. `audit_pointer_wake_v1.py`
checks pinned source bytes, within-pair initial image equality, terminal/owner cause
equality, recorded physical release checks, and all nine exact image frames. The
outer process handle completed with exit 0. Close calls returned for each executor,
backend, controller connection and session; no independent per-process inventory
is claimed. Transitive environment/package versions were not exhaustively pinned.
No formal domain adoption, token/cost improvement or Research Freeze follows.
