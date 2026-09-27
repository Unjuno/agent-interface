# Issue #4222 preformal plan

Allocation: `interrupt-stack-live-resume-4222-20260923-01`

## H
A saved interrupt frame is not sufficient authority to resume. After a real one-level Tk modal interruption, target replacement, queue-version change, stale source evidence, or pending UNKNOWN can make POP_ONLY continuation unsafe. EVIDENCE_BOUND_RESUME should resume only the unchanged current frame and otherwise refuse before suffix input.

## T
Fresh private authenticated TCP-disabled Xvfb and fresh Tk application per case. Real XTEST types prefix `a` before interruption and, only when policy says RESUME, suffix `b` after interruption. One owned Tk Toplevel is the interruption. Fixture mutations alter declared current state or replace Entry A but never type/delete the task suffix.

Policies: POP_ONLY / EVIDENCE_BOUND_RESUME.
Scenarios: NORMAL / TARGET_REPLACED / QUEUE_CHANGED / SOURCE_STALE / PENDING_UNKNOWN / TASK_CANCELED.
Two repetitions =24 sessions, split into immutable batch-0(rep0) and batch-1(rep1), 12 cases each. Formal batch rerun/replacement/tuning budget zero.

## D
PASS_INTERRUPT_STACK_LIVE_RESUME_SCOPED requires exact24 rows and process/source/input/effect integrity; both policies complete NORMAL; candidate refuses all four stale/unknown continuation scenarios before suffix input and has zero unsafe resumes; POP_ONLY exposes four unsafe resumes per repetition including a visible wrong-target `b` effect after TARGET_REPLACED; both stop TASK_CANCELED; refusals are unresolved/canceled, never success; all app/Xvfb exits0 and final key states neutral; raw-only audit errors=[]; >=10 coherent evidence mutations reject.

## C
Application state receipts are cooperative evidence, not authentication. Target replacement and state changes are barrier-directed. The modal is one Tk Toplevel, not a general OS/application dialog.

## U
No nested interrupts, real save semantics, actual lost-delivery ambiguity, model/planner benefit, tokens/latency, crash durability, arbitrary toolkit, natural race frequency, or production promotion.

## Construction retained outside formal
- construction-01: STOP_XAUTH_PARENT_MISWIRE before first complete case; parent Python-Xlib looked at default ~/.Xauthority instead of allocation-owned Xauthority.
- construction-02: 12 live cases completed, but after auditor hardening its old row-source audit hash correctly fails read-only re-audit; retained, excluded.
- construction-03: final source, 12/12 excluded cases, audit errors=[], POP_ONLY unsafe resumes4, candidate unsafe resumes0.
