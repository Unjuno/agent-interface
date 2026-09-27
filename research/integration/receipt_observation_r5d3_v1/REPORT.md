# Complete receipt observation — Issue #4361

## First-outcome disposition

**PASS_RECEIPT_OBSERVATION_BOUNDARY_SCOPED.** One prospectively source-frozen allocation, three first-outcome eight-case batches, 24 sessions and 48 distinct owner/reader subprocesses. No rerun, replacement, exclusion or postfreeze source/gate tuning.

This is a concrete result/recovery measurement boundary under #2789, not runtime promotion, model utility, generic IPC optimization or the completed global ROADMAP.

## Correction to predecessor #4231

At intake main `4a1f3957e91b412a64769199f78f2c4b0102d28b`, old owner.py blob `b57b81e58c6541dd7596f3c7119221baae83daef` samples receipt_ns before print. Old run.py blob `cd4fbc484a22b7b5ff53d297344899fe9fac36bc` trusts that field and performs stdout.read(), without a consumer timestamp. Calling the old numbers receiver arrival/delivery was too strong. Correction comment5832396571 preserves all old source/raw/results and narrows the endpoint to owner pre-output. The old study was not rerun.

The present study changes the scientific boundary to separately measured receiver read/validation completion. It does not retroactively supply missing old telemetry.

## H / T / D / C / U

H: an early producer stamp cannot certify complete receiver observation. Reader pause and a split frame can cross a receiver deadline. Conversely, waiting for EOF can delay a complete one-frame result while a writer remains alive.

T: actual anonymous pipe, separate READY-synchronized owner and reader processes. Two modes (UNTIL_EOF, COMPLETE_FRAME), four schedules, three repetitions each. Exact JSON-line schema/identity, integer timestamps, bounded4096-byte frame. Deadline200ms from common CLOCK_MONOTONIC origin. Effect target60ms, producer stamp/first write80ms, delayed read/final fragment/held writer close320ms. Three serial eight-case batches, reverse mode order in repetition1. No real task, GUI, input injection, model, provider, installation or experimental network.

D: every complete case reconciles exact transmitted/received/effect bytes, actor/request identity, syscall and effect-fsync brackets, validation/EOF order, source freeze and actual process exits. QUIET must be on-time in both modes; PAUSE/SPLIT late in both; HELD_OPEN late with EOF but on-time with complete-frame acquisition. All gates met. All13 non-noop controls reject normally. Missing/incorrect evidence remains a typed failure, never fabricated PASS.

C: one-shot trusted line-delimited protocol, single writer, same monotonic clock and no malicious peer. COMPLETE_FRAME is appropriate because the protocol defines exactly one complete frame; EOF may still be required by protocols whose validity depends on stream closure. No timed preemption at200ms is implemented: both readers report whether their actual complete validation met that deadline.

U: validation completion is not kernel arrival, model consumption, independent source authentication or current GUI state. The effect record's fsync bracket is a fixture observation, not power-loss durability. Scheduling/validation/recording overhead influences diagnostic times. Clock1ns reported resolution is not1ns calibrated accuracy; no calibrated combined uncertainty or population failure probability is invented. Same-author different implementation/process audit is not independent human review.

## Observed reader endpoints

All values below are milliseconds from each common start; each cell is three sessions. These are deliberately separated80/320ms exposures, not a throughput/latency-optimization benchmark.

| Schedule | Reader | Median | Observed range | On-time / late |
|---|---|---:|---:|---:|
| QUIET | UNTIL_EOF | 81.093700 | 80.947058–81.136211 | 3 / 0 |
| QUIET | COMPLETE_FRAME | 80.937081 | 80.929191–80.959065 | 3 / 0 |
| READER_PAUSE | UNTIL_EOF | 320.770401 | 320.755773–320.834699 | 0 / 3 |
| READER_PAUSE | COMPLETE_FRAME | 320.943186 | 320.690919–321.366908 | 0 / 3 |
| SPLIT_FRAME | UNTIL_EOF | 320.684260 | 320.678644–320.776456 | 0 / 3 |
| SPLIT_FRAME | COMPLETE_FRAME | 320.632661 | 320.570995–320.674306 | 0 / 3 |
| WRITER_HELD_OPEN | UNTIL_EOF | 320.655542 | 320.567917–320.709549 | 0 / 3 |
| WRITER_HELD_OPEN | COMPLETE_FRAME | 81.204383 | 81.001198–81.212203 | 3 / 0 |

Producer stamps and effect-fsync brackets precede200ms in all24 cases. Producer-stamp-only therefore falsely classifies15/24 actually late observations as on-time. These paired classifications are not additional independent experiments. EOF reader:3 on-time/9 late; complete-frame reader:6 on-time/6 late. The candidate's six late PAUSE/SPLIT outcomes remain late, not successful deadline completion. The three complete-frame HELD_OPEN observations precede owner close; all owners still exit normally. Early partial bytes are retained and never treated as a complete receipt.

## ERROR CHECK / evidence

The frozen raw-only auditor imports neither protocol nor actor nor runner:1460 checks, errors[],24 cases,48 unique actor PIDs. All48 actual actor exits and all3 runner/external exits are0. Audit PID874 and control PID875 returned0, with raw stdout/stderr hashes in VALIDATION_RECEIPTS.json. Thirteen effective copied-evidence controls cover missing case, identity, PID, receiver/writer/effect bytes, producer classification, observed clock, missing EOF, authority, packet identity, deadline and source change. Missing/malformed copies return typed errors; caught FileNotFoundError/IndexError names are preserved, not disguised as successful reads. All13 frozen files remain byte-identical.

Excluded construction:8 sessions/16 actors,483 raw checks,12 effective controls and9 unit methods passed. A separate prefreeze metadata helper failed because /proc/self/ns/time was absent; the exact traceback is retained. The collector records namespace information unavailable, not a fabricated namespace attestation. Construction was not pooled into the formal result or rerun.

## Environment / unit check

Supplied Linux6.18.44 x86_64/glibc2.41, CPython3.13.5, stdlib; Intel Xeon Platinum8370C nominal2.80GHz, five visible CPUs, recorded frequency snapshot2793.438MHz. No Docker/Podman/gh executable, so no image-attested Docker/OrbStack claim. Actual Python/stdlib hashes and boot identity are in ENVIRONMENT.json. Native integer CLOCK_MONOTONIC nanoseconds share the process clock assumption. Subtracting two timestamps yields duration in ns; division by1,000,000 yields the reported ms. Deadline200ms is200,000,000ns. PLAN/PROOF give the full variable table and conditional reasoning.

## Bounded roadmap / adoption decision

Intake/collision and original-source correction -> excluded construction -> exact public source capsule/readback at835ee200e7c5bbc3d381b1554f704c4371116f03 -> first3 batches -> raw audit/controls: complete. Evidence publication/PR/CI/main readback must be recorded separately and are not inferred by this local report.

For #2789 result/recovery: keep producer emission, complete receiver observation and effect commitment distinct. Do not use producer stamps or partial bytes to prove reader deadlines; do not wait for producer termination when the declared protocol already supplies a complete verifiable result. Neither receipt reading nor lateness grants retry/input authority. No new runtime feature is adopted here.

Related application ideas (unmeasured): HCI can distinguish available progress from confirmed completion; distributed-systems clients can distinguish emission from read completion; real-time control can keep measurement age and execution effect on separate endpoints. Each needs its own integration evidence.

Primary documentation: Python3.13 time (monotonic/per-process semantics) and io (EOF/readline). The actual process results, not documentation alone, support this experiment.
