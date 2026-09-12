# Local receipt tracing and combined action/image returns

`traced_client.py` launches the unchanged v7 adapter with pipes and records
command receipt, child event receipt and stdout write completion in the same
WSL monotonic clock domain as the runtime. It forwards complete event records;
it never selects actions, changes deadlines or automatically renews authority.
The manifest pins wrapper/entrypoint sources before startup. Child sources are
pinned separately by the runtime.

The client also writes an atomic latest-feedback convenience file. This is NOT
an event queue or sufficient critical-event history: full stdout and client.jsonl
remain the authoritative delivery record. An observation may arrive before a
terminal; callers must inspect status and sequence, not treat an image as action
completion. Synchronous tracing and feedback writes perturb timings. This wrapper
is measurement scaffolding, not a production transport or crash recovery design.

## Actual operation

In `traced-assistant-01`, seed990701, each functions call sends an action, reads
feedback and emits the referenced PNG before returning to the model. No separate
model turn is needed solely to request the image. Full runtime events are still
included; no compact projection is enabled. The first returned image showed the
target left of center. The assistant turned Left100ms, inspected the resulting
image in that action's return, then fired Space350ms. The next return showed
FINISHED; only then did the assistant send finish. Post-control scoring confirmed
finished/alive. No engine telemetry selected actions.

Eight frames reconstruct exactly, two programs complete with verified release,
owner closure is verified, and every raw/delivered record equals the client's
received record in order. The wrapper's command stream matches runtime receipt.
Run `python research/doom/audit_traced_client.py` to reproduce those checks and
the endpoint calculations.

## Observed endpoints, not a comparative speed claim

| Endpoint (milliseconds) | Aim | Fire |
|---|---:|---:|
| Client command receipt -> runtime acceptance | 31.328 | 14.155 |
| Acceptance -> first local image ready | 182.874 | 85.755 |
| First image ready -> local client receipt | 9.560 | 63.103 |
| Combined tool-call body (send, feedback read, image load) | 1960 | 2175 |

The first returned fire observation reused the earlier scene. Therefore its
85.755ms image-ready time is not evidence of useful shot feedback. Later frames
showed the finish screen; semantic completion time and model recognition receipt
are still not instrumented.

Runtime acceptances were **12.384s apart**. A separate wall-clock trace inside
functions recorded **10.444s from the first image tool's return to the next
functions call body starting**. This interval includes result delivery, model
processing and orchestration; it is not a pure model inference measurement.
The measured combined call body was about2s, with roughly1s intentionally spent
waiting in write_stdin and another0.8–1.1s reading/loading feedback. It excludes
the outer functions response transit and model receipt. Do not subtract absolute
timestamps across the WSL monotonic and functions Date.now clock domains.

This evidence locates substantial remaining time outside local runtime image
generation and pipe receipt in this run. It does not establish one causal source
for the whole gap. Seeds, aim difficulty, action sequence and instrumentation
differ from earlier runs; do not claim a percentage improvement from22s to12s.
Actual model identity/usage accounting and tokens are not captured here.

## Decision and next comparison

Retain the tracing scaffold and combined-return pattern for further experiments;
no core semantic change or performance promotion. A bounded follow-up should
compare separate versus combined image return with the same model/settings,
task allocation and feedback policy, counterbalanced order and declared success
gates. Instrument outer tool/model receipt if available, or keep that interval
explicitly unresolved. Avoid reducing wait time blindly: an earlier return can
increase polling and expose incomplete observations. Measure critical event
delivery and task correctness along with timing. The black-screen investigation,
cross-domain validation and original human-tempo goal remain open.
