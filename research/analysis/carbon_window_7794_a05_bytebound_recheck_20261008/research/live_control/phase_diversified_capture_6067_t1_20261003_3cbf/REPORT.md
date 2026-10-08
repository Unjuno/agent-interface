# #6067 T1 A01 formal result

**STOP_CAPTURE_TIMING_GATE**, not scientific PASS or evidence against the
phase-diversity hypothesis. Candidate1 / formal auditor0. Allocation A01 is
consumed; no retry or replacement, no pulse-comparison cells executed.

Source48ce12d529c1a9127e46eda4b33bcaaa278129a2;
prospective freeze6990c3e2650b34f557ba11f51949f9bcc5b1ee41,
issue comment5968687263, published before start.
Guest source hashes matched both before and after the one formal block.
Command, exact image, limits and terminal Docker receipt are retained.

Formal container ran 2026-10-03T11:23:34.346692577Z to
11:23:37.494942063Z, terminal exit2, OOMfalse/restarts0.
Observed cgroups CPU1/memory512MiB/swap0/PIDs64. No model or input.

| Retained control | Frames | Maximum start lateness | Child exits | Gate |
| --- | ---: | ---: | --- | --- |
| c000 fixed dark | 8 | 1.550538ms | 0/0/0 | complete |
| c001 irregular dark | 8 | 17.231413ms | 0/0/0 | STOP |

c001 first acquisition was due at epoch+15ms and began17.231413ms late;
XGetImage itself took0.223959ms. Remaining seven starts were at most0.020594ms
late. The break preceded native acquisition. All16retained frames were dark
and decoded no cue. Positive controls and all108phase-width comparisons are
unreached; no all-miss comparison counts or benefit estimate can be reported.

The 15ms final-spin pacing that qualified native02 static controls did not
guarantee the admitted formal timing budget. Timer-only qualification is not
native full-matrix qualification. Kernel/host scheduling, CPU-period quota,
or first-deadline descheduling are possibilities, not established causes.
Per-deadline CPU throttle/scheduler traces were not collected and cannot be
backfilled. The small native call cost alone does not identify the wake cause.
The unprivileged Xvfb socket-directory warning is retained but not shown causal.

## Preserved failures and review corrections

Native01 sleep-only construction STOP10.234570ms; excluded timer comparison;
prospective15ms spin; native02 static qualification; pre-freeze independent
HOLD with source chronology/typed-journal defects; effective red→green repairs;
and this first formal STOP are separate immutable checkpoints.19pure methods
pass but do not complete T1. Main/public runtime is unchanged.

## Integration and continuation boundary

Retain the executed negative evidence and source/receipt checker by reviewed PR.
Do not close parent #6067 as scientifically completed. #57/#59 remain open.
Any next native phase attempt must be separately named and prospectively admitted
after timing/allocation requalification with source-clock and per-deadline
resource telemetry. Do not relax10ms or overwrite A01 to manufacture a result.
No shared/default engine, peer allocation, physical-host exclusivity, input,
model, task effect, per-key release, recovery or safety inference is authorized
by this artifact.
