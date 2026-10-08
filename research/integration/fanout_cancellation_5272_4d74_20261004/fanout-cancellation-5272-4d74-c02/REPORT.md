# #5272 cancellation accounting boundary

Decision: SUPPORT_TERMINAL_RELEASE_ACCOUNTING_SCOPED / HOLD_REAL_VERIFIER_BENEFIT.
One fresh WSLc candidate invocation and one separate same-author saved-only
event-state audit both exited 0. The auditor labels its finite method gate
METHOD_PASS_SCOPED; it is not #5272's scheduling/latency PASS criterion.

Six authored behaviors, two accounting policies, twelve actual asyncio cells:
request-only refunded the optional slot while the original coroutine remained
live in slow_cleanup, suppressed_late and mandatory_unfinished (3/6 cells).
Terminal+release accounting had no original/replacement overlap (0/6).
Slow cleanup and suppressed cancellation took about 40 ms after cancellation;
sealed FAIL did not change when a late PASS result appeared. Mandatory unfinished
remained UNKNOWN in both policies. Missing fixture release retained a slot HOLD
under terminal+release; it does not prove a real external resource leaked.

The decisive FAIL/UNKNOWN is authored at the scheduling boundary, not the output
of an actual mandatory verifier. Replacement coroutines really run. The optional
resource is a logical single coroutine slot; there is no semaphore or production
scheduler here. The completion_race case is deterministically complete-before-
cancel using an event/join, not a sampled OS race. Cooperative means prompt
termination after cancellation; the worker catches cancellation and returns.
Both policies share behaviors and nominal durations, run sequentially in fixed
order, and are single exposures. No causal latency superiority, rare-race rate,
backend termination/reclamation, task quality or economic claim follows.

The stronger simple reference is joining the actual task and requiring its
explicit logical release receipt before refund. This suffices for the exposed
fixture boundary; no new cancellation mechanism or complex scheduler is needed.
Do not promote request/timeout into a physical release or budget refund. Actual
verifier adoption remains HOLD until a qualified implementation can provide its
owned terminal/release oracle, mandatory evidence, measured useful work, costs
and deadlines. Stop further cancellation-stub variants as a substitute.

First launch C01 was STOP_UNSUPPORTED_LAUNCH_OPTION: WSLc rejected --read-only
before invoking Python. All source/freeze/command/stderr/empty stdout/exit bytes
are retained in sibling package, unchanged. C02 is a separately recorded launch
with identical candidate/auditor/plan/freeze source, removing that unsupported
option. /study is mounted read-only; root filesystem is not claimed read-only.
This is routine launcher correction, not retry of a consumed formal study.
Prior #5272 preparation STOPs and their allocations remain unchanged.

Python 3.12.15, pinned Debian image f649ccab8aec3b94e451c6b0037e60fca72d7d7559381f8cd4aa98530b786c55;
network none, UID65534, CPU1/memory512M requested. Producer sampled cpu.max
100000 100000 and memory.max536870912; pids.max=max. Retained swap-limit
warnings from producer/audit do not establish host-wide resource isolation.
No GPU/model/browser/native input/app effect/provider invocation.
Base/source intake main 0f0f17e6c646f0856173f54d31df7a0dc87fa49c.
No production runtime source is imported or modified.
