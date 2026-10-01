# C6T9: affine clock/deadline contract, local analytical verification

Date: 2026-09-25 JST. Allocation: affine-clock-c6t9-20260925-01.
Intake main: b669264a65d1474481e511676eacfc06bf82d775.
Potential additive path: research/analysis/affine_clock_deadline_c6t9_v1/**.
Potential branch: research/affine-clock-deadline-20260925-c6t9.
Both are LOCAL proposals, not remote reservations or created resources.

## Motivation and preserved predecessors

The existing r4m8 proof assumes comparable clocks and explicitly leaves justified
clock-error bounds open. #4345 owns LIVE X11 witness lifetime; do not run it.
#1859 explicitly warns that its exact clock mapping may not suffice for drifting
clocks. #3880/#3886/#3919 concern measured host/container lease and send transport.
This study does NOT redo those live studies or their production validators.
It changes the mathematical model to a positive bounded affine clock with several
simultaneous interval-calibration constraints and studies exact release projection.
No old outputs, freezes, branch or runtime files are modified or pooled.

## H

Under the explicit affine/epoch/horizon/single-release assumptions, exact joint
projection yields the full possible release interval and sound ON_TIME/LATE/
UNRESOLVED decisions. A nominal feasible clock can falsely certify timing; an
independent marginal clock box remains conservative but can unnecessarily abstain.
Empty/inconsistent/missing/invalid evidence never produces a definite certificate.
The analytical theorem is proved before the executable finite check.

## T

Provided Linux container; installed CPython3.13.5 stdlib/Fraction, exact rational
strings. No GUI/input/model/provider/experiment network or package installation.
No Docker/OrbStack image attestation or live-clock calibration. No runtime import.

Construction:16 focused unit methods, separate receipts. Fixtures include the
same directed analytic examples for boundary rehearsal; they are NOT held-out
experiments and are not added to the main denominator.

Generate and freeze INPUTS.jsonl without evaluating its full corpus. Grid:
3 rate intervals *3 offset intervals *6 first sample brackets *6 second sample
brackets *4 release intervals *7 deadlines =9072, plus16 directed cases =9088.
Sample coordinates0 and2; exact rational bounds/negative reference times included.
See corpus.py for complete deterministic enumeration; no random seed required.

Freeze candidate, corpus, independent vertex auditor, controls, tests, proof,
plan, inputs and environment locally before ONE new run_check.py invocation.
A GitHub public preregistration is NOT claimed: this session exposes read tools
only and no authenticated CLI. Capture actual outer command/exit/time receipt.
Use bounded invocation with generous outer allowance; no retry/replacement/tuning
or completion of any consumed GUI allocation. Stop and retain partials on failure.

## D

PASS_LOCAL_AFFINE_CLOCK_CONTRACT requires all9088 ordered exact inputs/outputs,
complete process/source evidence, candidate vs independent 2D-polytope oracle
agreement, correct open/closed deadline equalities and empty/invalid refusals,
positive nominal false-ONTIME and false-LATE examples, at least one marginal-box
UNRESOLVED that exact joint projection resolves, no output authority/task-success,
all16 unit methods and12 effective copied-evidence corruptions rejected.
Complete disagreement is FAIL_CONTRACT; missing source/rows/process/controls is
HOLD/STOP. Source identities and original first outcomes remain unchanged.

## C

Known interval/linear-optimization methods, not a new clock algorithm. Bounds are
assumed; calibrations constrain but do not establish the affine model. A declared
non-affine counterexample must be retained. Numeric exactness is not uncertainty
calibration. Feasible nominal comparator is authored, not deployed code allegation.
Paired classifications of one synthetic input are not independent samples.

## U

Real calibration, drift/jitter/quantization, suspend/resume/restart, clock identity
and authentication, multiple transitions, application/physical HID, hard deadlines,
model/task/latency/token benefit and runtime adoption are untested. Same-author
separate auditor is not independent external review. No confidence or u_c/k.

## Roadmap / integration decision

1. Restore r4m8 read-only and confirm no old GUI or candidate reruns.
2. Check main/direction/open-closed issues/PRs/branches and exact clock overlap.
3. Prove projection; construct16 unit checks; freeze full inputs/source/gates.
4. One9088-row local computation; independent oracle;12 effective controls.
5. Complete additive artifacts, read-only reconstruction, patch plus unposted
   successor/Issue-comment/PR drafts. Publication remains pending without writes.
6. Only a qualified future current-path validation can promote the certificate;
   prerequisite: justified clock relation over its validity horizon. Keep #4345,
   #3066, #3880 and global roadmap outcomes separate. No branch deletion unless
   a supported action and complete dependency evidence permit it.

Concrete #2789 integration boundary: never collapse a clock uncertainty set to a
point before deciding whether observation/release met a deadline. Preserve joint
clock constraints when available, otherwise stay unresolved rather than inventing
certainty. This is a measurement/recovery contract, not a control-policy change.
