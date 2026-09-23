# Issue #4222 — live one-level interrupt resume

**Decision: `PASS_INTERRUPT_STACK_LIVE_RESUME_SCOPED`**

The prospectively frozen allocation completed 24/24 fresh Tk/Xvfb sessions in two immutable 12-case batches. Formal reruns/replacements/post-freeze tuning were 0/0/0. The separate raw-only auditor returned errors=[], and all 12 coherent corruption controls rejected.

## Result

| scenario | POP_ONLY | EVIDENCE_BOUND_RESUME |
|---|---|---|
| NORMAL | RESUME 2/2, A=`ab` 2/2 | RESUME 2/2, A=`ab` 2/2 |
| TARGET_REPLACED | RESUME 2/2; replacement A=`b` 2/2 | `REVALIDATE_TARGET` 2/2; suffix input 0 |
| QUEUE_CHANGED | RESUME 2/2; unsafe continuation 2/2 | `REPLAN_QUEUE` 2/2; suffix input 0 |
| SOURCE_STALE | RESUME 2/2; unsafe continuation 2/2 | `YIELD_STALE` 2/2; suffix input 0 |
| PENDING_UNKNOWN | RESUME 2/2; unsafe continuation 2/2 | `RECONCILE_RESULT` 2/2; suffix input 0 |
| TASK_CANCELED | `CANCELED` 2/2; suffix input 0 | `CANCELED` 2/2; suffix input 0 |

Candidate unsafe resumes: **0**. POP_ONLY unsafe resumes: **8**. All application and Xvfb exits were 0; every final observed test key state was neutral.

## H / T / D / C / U

- **H:** a saved interrupt-stack frame is continuation context, not sufficient evidence to resume after target/queue/source/result state changes.
- **T:** real XTEST task prefix/suffix input, one ordinary owned Tk Toplevel interruption, fresh authenticated private Xvfb and application per case, six schedules, two policies, two repetitions.
- **D:** the evidence-bound contract preserved the two valid resumes and stopped all directed stale/unknown resumes before suffix input; exact raw audit and corruption gates passed.
- **C:** current-state receipts are cooperative fixture evidence. The state mutations are barrier-directed. More evidence fields are intrinsic to the contract under test, not a free efficiency comparison.
- **U:** nested interrupts, arbitrary dialogs/toolkits, real save semantics, actual lost-delivery ambiguity, model/planner behavior, latency/tokens, crash durability, natural race frequency and production integration remain untested.

## Retained construction

- construction-01: `STOP_XAUTH_PARENT_MISWIRE` before a complete case.
- construction-02: completed 12 excluded cases; after preformal auditor hardening, read-only re-audit correctly flags its now-old audit.py row hash.
- construction-03: final source, excluded 12/12, audit errors=[], POP_ONLY unsafe=4, candidate unsafe=0.

## Integration handoff

A stack `pop` must not restore input authority. After an interruption, current task liveness, pending-result disposition, source freshness, queue version and target identity must be revalidated before resuming the remaining task effect. Refusal remains unresolved/canceled rather than being counted as successful recovery.

This is a scoped live-fixture result, not completion of #2869/#2789 or the repository ROADMAP.
