# Issue #3945: neutral input is not an application-queue drain

## Decision

**PASS_APP_QUEUE_NEUTRAL_BOUNDARY_SCOPED** for the one frozen allocation
`app-queue-neutral-retry-20260922-01`. Fifteen first sessions completed; formal
invocations 1, reruns 0, replacements 0, exclusions 0. The independent raw-only
auditor exited 0 with no errors and rejected all 12 corruption controls.

This is a result/recovery boundary, not a production implementation or a model
quality, performance, token-saving, exactly-once or Docker/OrbStack claim.

## H / T / D / C / U

**H.** Server-confirmed button release and a currently unchanged application
counter do not prove failed delivery or successful cancellation when the
application has not yet consumed the queued input. Blind retry of a
non-idempotent action can duplicate its eventual effect.

**T.** A fresh ordinary Tk Button application runs in its own process on an
allocation-owned Xvfb. The controller pauses only the application with SIGSTOP;
the server remains live. Real XTEST press/release and a separate X connection
establish physical input state. Only the button's unmodified class-bound command
increments its own counter file. The controller cannot invoke that callback.
After the paused snapshot, a blind-retry control sends a second click; the
pending/no-replay candidate does not. SIGCONT and an application idle fence
allow the already queued input to finish. Five scenarios, three fresh sessions
per scenario, fixed order; no model/provider or host-desktop input.

**D.** All frozen row, process, source, event, on-disk counter and neutral-state
gates pass. The positive control remains usable; pending effects occur only
after application resumption; blind retry duplicates; no-replay preserves one
commit. All cleanup and raw-only audit gates pass. The unsafe control's result
is intentionally a duplicate; it is not a successful cancellation.

**C.** The injected pause is barrier-controlled, not a natural stall-frequency
sample. The protocol chooses UNKNOWN/pending explicitly; no model learned that
choice. An idle fence here checks this finite fixture; it is not a generic
cross-channel completion barrier. Journals and counter files expose the same
fixture callback, not two independent physical-world effect measurements.

**U.** Native desktops, other toolkits, power-loss durability, process crashes,
unknown callback side effects, authenticated client isolation, policy utility,
real cost/latency benefit, and a production exactly-once recovery protocol remain
untested. Missing distribution metadata for python-xlib is disclosed, not filled
with an invented package version.

## Retained first outcomes

| Scenario | Sessions | Effects before resume | Final effects per session | Disposition |
| --- | ---: | ---: | --- | --- |
| LIVE_ONCE | 3 | Not a paused-state gate | 1, 1, 1 | Positive control |
| PAUSED_ONCE | 3 | 0, 0, 0 | 1, 1, 1 | Delayed application consumption |
| PAUSED_BLIND_RETRY | 3 | 0, 0, 0 | 2, 2, 2 | Duplicate-effect negative control |
| PAUSED_PENDING_NO_REPLAY | 3 | 0, 0, 0 | 1, 1, 1 | UNKNOWN/pending; no second click |
| PAUSED_NO_INPUT | 3 | 0, 0, 0 | 0, 0, 0 | No-input control |

All nine paused click sessions had a /proc-confirmed stopped application,
responsive neutral X server, and zero current effects before resumption. All
15 final input states were neutral. There were 15 task clicks and 15 separately
recorded unconditional cleanup-only ButtonRelease requests. All 15 application
processes and the private Xvfb exited 0 and were reaped. A later /proc check found
none of those owned PIDs alive. No other process or branch was stopped or reset.

## Evidence and independent reconstruction

`formal-01/RAW.json` retains controller requests/responses, actual application
journals/counter bytes, process pause evidence, X-client resource ranges,
press/release queries, app/server exit status and the frozen source map.
Original per-case files are also retained. The auditor imports neither runner
nor application and independently checks ordering, identities, exact effects,
raw-file joins, booleans versus integers, and source/freeze bytes.

The 12 corruption controls cover missing/duplicate cases, changed counter bytes,
changed effect journals, lost pause proof, false DONE, missing release evidence,
false-neutral masks, Boolean exit codes and effect counts, wrong application
identity, and wrong scenario. Passing these finite controls is not a proof of
arbitrary auditor soundness. Audit independence means a separate implementation
and process, not a separate human researcher.

| Artifact | SHA-256 |
| --- | --- |
| FREEZE.json | f7c13b7c24011d9946e2b3de564f39909872e33cbde143cb853c8c23c6ac6785 |
| formal-01/RAW.json (217,548 bytes) | 5b8f36167f6c97194f4d61d3682c205bb74f0e762e070cfd3732c6750713d3fc |
| AUDIT.json | e3ae23d911f7f0f4b02476d4c24ed29bc66b7fb7393b7c86d15c2521ecf56378 |

The frozen source map was rechecked 7/7 after formal execution. Formal raw bytes
were identical before and after the independent audit. No source, threshold or
formal result was corrected after the result was observed.

## Failures preserved, not pooled

Construction-01 stopped before task input because python-xlib inherited a
nonexistent XAUTHORITY file. Its first raw record, traceback, exact source,
zero counter and cleanup are retained. The Issue explicitly amended the
construction budget before construction-02; this is not hidden as compliance
with the original one-session wording. Construction-02 completed five sessions
and its own construction-only audit. A metadata-only environment capture then
hit PackageNotFoundError; the final environment record preserves the missing
distribution metadata and records imported-module and binary/source identities.
Neither incident is a formal result or a reason to replace a formal session.

## Environment and publication boundary

Provided Linux x86_64 execution container, CPython 3.13.5, Tk 8.6.16, private
Xvfb with TCP disabled, installed python-xlib and native XTEST. Exact installed
binary/module hashes and package outputs are in ENVIRONMENT.json. Docker CLI
was unavailable. No network call was made by the experimental scripts; this is
not a claim of Docker-enforced network isolation. The empty local Xauthority
file is not an authenticated-client isolation guarantee; warnings are retained.

Intake and pre-formal main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Additive namespace: `research/integration/app_queue_neutral_retry_v1/`.
Parallel #3930 (abort acknowledgement), #3936 (widget-phase cancellation),
#3934 (scheduler affinity) and event-reader studies were not modified.

## Roadmap and integration handoff

The bounded scientific roadmap is complete: lineage/collision check, declared
H/T/D/C/U, excluded construction, source/environment freeze, one formal block,
independent raw reconstruction and corruption controls, immutable evidence
packaging. PR/main delivery is tracked in the GitHub discussion, not inferred
from this local report.

The integration requirement is: **do not convert an unchanged current effect
observation plus physical neutrality into FAILED_DELIVERY/CANCELLED, or blind
permission to replay a non-idempotent action while application consumption is
unresolved.** Require appropriate application evidence or an explicit
idempotency/recovery contract; preserve UNKNOWN/pending otherwise. This study
validates the counterexample and bounded no-replay behavior, not a general
solution for acquiring that evidence.

#2197, #2204, #3193, #2789 and the repository-wide ROADMAP remain open. This
result does not close their model-facing, cross-application or integrated
quality/cost acceptance gates. Do not rerun the consumed formal allocation or
execute prepare_freeze.py over retained evidence. Any live successor needs a
new Issue/allocation, fresh directory, independent gate and source freeze.
