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
