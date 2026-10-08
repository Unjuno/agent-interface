# #1465 preformal construction report

Task: `CONCURRENT-FAST-DECISION-T2-RAW-RECEIVE-LINEARIZATION-A10-20260918-013`

Status: **construction eligible / nonformal stress PASS-shaped / formal 0**.

This successor isolates the latest #1449 boundary defect. The predecessor performs blocking `recv()` before taking the authority mutex. The candidate takes the authority mutex only for a nonblocking readiness check and, when readable, keeps that mutex across `recv()`, the first post-return monotonic timestamp, and local-generation closure. Waiting polls release the mutex immediately.

## Retained first construction

The first raw construction file was run once. It contains one forced predecessor discriminator and four candidate cases using the inherited state programs.

Scientific/mechanism observations from that raw file:

- predecessor admitted **1** boundary probe after actual receive return and before authority close;
- predecessor admitted gap was **94.325 us** after the first post-`recv()` timestamp in this retained run;
- candidate admitted **0** commits at/after actual receive return across 4/4 cases;
- candidate boundary probe rejected **4/4** after waiting on the authority lock;
- candidate preserved **5** pre-return lane admissions;
- terminal generation/closure, child exit and thread cleanup were exact in all candidate cases.

The 2 ms post-receive pause is an adversarial construction device, not a latency target. It is intentionally outside the mutex for the predecessor and inside the mutex for the candidate.

### Retained audit defect

The first audit invocation returned `FAIL_INTEGRITY` even though its science checks were clean. The defect was in one corruption-control expectation: moving a boundary probe from `rejections` to `admissions` correctly caused the independent evaluator to reject the mutated result, but the control demanded one specific failure class (`FAIL_RAW_RECEIVE_AUTHORITY`) while the evaluator gave higher-precedence shape-integrity failure.

No construction raw was rerun. The auditor was changed only so this corruption control requires rejection rather than one exact rejection class. Re-auditing the same raw gives `PASS_CONSTRUCTION_ELIGIBLE`; 5/5 corruption controls reject their mutations. The original failed audit is retained.

## Bounded nonformal stress

After the same raw construction passed the corrected and independently structured audits, one bounded nonformal stress run executed 500 fresh candidate cases with fixed seed `146520260918013`.

Result:

- candidate cases: **500**;
- post-raw-receive admitted commits: **0**;
- boundary-probe rejections: **500/500**;
- pre-return lane admissions: **616**;
- primary corruption controls: **4/4** rejected;
- independently structured audit: PASS, errors `[]`.

Descriptive timing under the stress harness (includes an intentional 0.25 ms in-lock post-receive pause):

| measurement | median | p95 | max |
|---|---:|---:|---:|
| child send -> userspace raw receive timestamp | 0.355370 ms | 0.533739 ms | 5.581737 ms |
| raw receive timestamp -> authority close | 0.338630 ms | 0.362676 ms | 0.824241 ms |
| boundary probe lock-attempt -> rejected commit | 0.349116 ms | 0.437138 ms | 2.319323 ms |

These are harness/scheduler measurements, not production benchmarks and not a speed claim.

## Environment

- Python: CPython 3.13.5, GCC 14.2.0 build
- Kernel: Linux 6.18.44 x86_64
- visible container CPUs: 5
- reported CPU model: AMD EPYC 9V74 80-Core Processor
- batch: construction 1 predecessor + 4 candidate cases; stress 500 candidate cases, sequential case schedule with one fresh child process per case

CPU frequency, host contention and scheduler placement were not controlled and are **UNKNOWN**. No model, network, GUI, X11, task input or shared runtime was used.

## Scope / interpretation

The construction falsifies the predecessor boundary under a deliberately widened post-receive window and shows that the candidate lock ordering closes that specific userspace interleaving while still admitting useful work before return. It does not establish a production ABI, kernel-arrival semantics, physical actuation cancellation, provider latency benefit, task usefulness or human-tempo operation. In-flight actuation completion is separately covered by #1459.

Formal status remains **0 invocations / 0 reruns / 0 replacements / 0 tuning**. A formal 20-case allocation requires a separate exact-head lease on #60.
