# Ordered relay host timeline (opt-in)

`relay_host_timeline_v1.mjs` wraps the existing persistent relay client with a
single-host event stream. It adds no model, sensor, task selection, retry or action
queue. Use `createInstrumentedRelayClient` with the same explicit command, args
and fresh evidenceDirectory as `createRelayClient`.

```js
const client = await createInstrumentedRelayClient(options);
await client.send('interface_guarded_observe'); // local attempt 1
await client.present(1, { text: nodeRepl.write, image: nodeRepl.emitImage });
// After viewing the image, explicitly declare the review:
await client.review(1, { task: 'task-1', phase: 'grounded', reason: 'Viewed field and Save.' });
// Decide the next operation from the image; no automatic action follows review.
```

Attempt numbers identify local `request-N.json`/`reply-N.json` files, not reused
relay protocol IDs. `wait()` returns the same send promise; it never resends.
Presentation reads only a delivered attempt's retained reply. Review derives the
call/source/image identities from that same file and writes `review-N.json`
exclusively. A later historical reply may be reviewed explicitly; this is not a
freshness or semantic admission gate. No automatic review is generated.

`host-events.jsonl` contains increasing sequence numbers and
`performance.now()` values from this host process. Events distinguish:

- `send_requested`: recorded before delegating to the relay client; not actual
  native emission. The client subsequently persists its request and writes stdin.
- `reply_available`: raw reply has been retained and its hash recorded; the
  response can now return to the caller.
- `presentation_started` and `presentation_callbacks_completed`: callbacks for
  retained text/image blocks start and finish. Completion is not screen rendering,
  model ingestion, useful feedback, understanding or semantic completion.
- `review_recorded`: caller declaration persisted with exact reply/call/source
  identity. Sequence order distinguishes review from the next send without file
  timestamp comparisons. It does not certify visual understanding or task success.
- `transport_closed`: child close returned, not GUI cleanup.

Only one wrapper operation can be outstanding. An overlapping send, present,
review or close refuses instead of queueing actions. A logging or callback error
blocks further actions; transport close remains possible for cleanup. Failed
operations may leave only a start event or a receipt with no completion event.
Never promote that partial evidence to completion. If an error follows sending,
input delivery may be uncertain; reconcile retained evidence without replay.

The timeline is opt-in because filesystem writes add overhead. There is no
fsync/crash durability, restart recovery, cryptographic authentication, model-token
accounting or cross-clock mapping. Clock values are comparable only within this
host lifetime. Treat ordered host boundaries as instrumentation, not a speedup.

Tests: `node --test research/live_control/test_relay_host_timeline_v1.mjs`.
## Read-only timing summary

After a host run, use `python3 -m runtime.integration_checks.host_timing /absolute/transport`
from the repository root. It reads the timeline and its hash-bound request/reply/review
files without invoking a transport or modifying evidence. Output contains per-call
send-to-reply, send-to-first-completed-callback, caller-declared review timing and
reply-to-next-send gaps, plus the exact input hashes. Missing completion boundaries
remain null/partial; malformed order or identity is an error, not a successful result.
Repeated presentation is retained and does not replace the first callback boundary.
Reviews without prior completed presentation are explicitly marked as such.

Use only one retained host lifetime per invocation. These are host boundaries,
not model ingestion, useful feedback, semantic completion, token accounting or
comparable speedup. `timeline_status=complete` means all recorded operations ended
and transport close was recorded; it does not imply successful process exit,
GUI cleanup or task success. See the retained [primary-use timing report](../../runtime/results/host-timing-summary-01/README.md).


Pre-dispatch relay refusals have no echoed `id` or `tool`: the reader binds them
to the pending local attempt, retained request, unchanged `next_id` and reply hash.
They contribute to send/reply time and carry `relay_outcome.status=refused` with
`dispatched=false`. A later corrected request can use the same protocol ID while
its local attempt number advances. Unknown dispatch outcomes retain
`relay_outcome.status=unknown_requires_reconciliation`; they are never inferred
to be no-input refusals. `returned_count` counts retained replies of all these
kinds, not successful backend actions. Neither a reply nor a timing result
authorizes replay. See [real relay regression evidence](../../runtime/results/host-timing-refusal-01/README.md).
# Public capture review receipts

`client.review(attempt, {task, phase, reason})` also accepts ordinary public
observe/dispatch images and management responses containing a returned
observation_report, such as explicit recovery or target review. It records a
v2 public-capture review receipt, with the exact reply hash, delivered image hash,
configured target/frame/region and capture timestamps. The image bytes must match
the declared artifact hash. Missing images or incomplete identities refuse.

Public captures have no server-issued observation sequence: source_sequence is
null, and dispatch images may also have a null observation_id. Do not substitute
a caller sequence or relay attempt number. Existing guarded/native v1 receipts
are unchanged. Use present first, explicitly review the delivered image, then
record the caller's reasoning; the record itself does not prove human/model
attention, semantic completion or first useful-feedback timing.

[Retained-response validation](../../runtime/results/public-review-recorder-01/README.md)
checks five real Calc image replies and rejects three replies without images.
This offline recorder check is separate from the earlier live primary decisions.

The read-only timing summarizer accepts both v1 and v2 public review declarations.
Public declarations must keep source_sequence explicitly null in both receipt and
event. [Primary live use](../../runtime/results/public-review-live-01/README.md)
retains a real Calc task, setup failure, caller mistakes, delayed visual updates,
and the initial summarizer incompatibility. Timings remain host boundaries.


## Partition the recorded host span

For complete nonempty timelines, `time_partition` divides first-send through
last-reply into request-outstanding intervals, presentation-callback intervals,
and other host intervals. Every presentation is clipped to that named span;
presentation/review/close after the final reply is excluded. Repeated
presentations are counted separately. Partial or empty timelines return null
rather than presenting incomplete accounting as a complete partition.

The categories are disjoint host-clock boundaries, not causal attribution.
Request-outstanding time includes transport/server/persistence work. Other host
intervals include orchestration, logging, caller review and gaps; they must not
be labelled model thinking, inference latency or idle waste. A high other share
does not establish that reducing it preserves task correctness. Existing
per-call boundaries and exact evidence hashes remain available.
