# Sequential relay host API

These two Node.js ES modules expose the already exercised relay client and optional host instrumentation outside the research tree. They use only Node built-ins and launch an explicit command supplied by the caller. Copy `relay_client.mjs` and `relay_host.mjs` together to use them outside a checkout. They are separate host files, not Python zipapp entries, and require Node.js 22 or newer. The execution relay can be the portable Python archive; see [public MCP transport](../cli_v1/MCP.md).

```js
import { createInstrumentedRelayClient } from './relay_host.mjs';
const client = await createInstrumentedRelayClient({
  command: '/absolute/python',
  args: ['/absolute/runtime.pyz', 'relay', '--',
    '--targets', '/absolute/targets.json',
    '--output-directory', '/absolute/new-server-records',
    '--session-mode', 'persistent-x11', '--display', ':99'],
  evidenceDirectory: '/absolute/new-host-records',
  minimumEvidenceFreeBytes: 32 * 1024 * 1024,
  reuseReviewedImages: false,
});
const response = await client.send('interface_observe', {
  target: 'editor', frame: 'screen_physical_px', region: [0, 0, 800, 600],
});
await client.present(response.attempt, {
  text: async value => { /* deliver metadata to the primary agent */ },
  image: async ({ bytes, mimeType }) => { /* deliver the same reply image */ },
});
// After actually reviewing the delivered image:
await client.review(response.attempt, {
  task: 'edit', phase: 'observe', reason: 'Describe the state actually reviewed',
});
// Use explicit per-call response bindings; do not review mutable latest state.
// Before EOF, send interface_close and inspect its release/cleanup outcome.
const closed = await client.send('interface_close', {});
await client.present(closed.attempt, { text: async value => {}, image: async value => {} });
await client.close();
```

The host creates `evidenceDirectory` exclusively. Supply a path that does not exist; do not create that directory before constructing the client. Keep the returned client in a durable caller binding before starting subsequent presentation work.

[The main integration record](../results/presented-host-main-01/README.md)
retains the missing-API stop, the source-frozen personal recovery trial, and
original replies/images. Its extra clock request and image preview are counted;
it does not establish a matched speed or token improvement.

`sendPresented(tool, args, {text, image})` explicitly composes one request with
presentation of its original reply. Both callbacks are checked before dispatch
and snapshotted before waiting. The host owns the full send/presentation interval:
another send, review or close cannot slip between them. `wait()` returns the same
pending promise; it never resends. A presentation failure retains the original
reply and blocks further ordinary input. Direct transport `close()` remains
available after a failure. This is synchronous sequencing at the caller API,
not a background queue, automatic replay or proof that pixels were understood.

After reading a presented text-only response, callers may use
`acknowledgeText(response.attempt, {task, phase, reason})`. It writes a separate
text acknowledgment bound to the unchanged original reply and completed
presentation, including any original MCP error flag. It sends no new request,
cannot stand in for image review, and grants no input authority or task success.
Image-containing replies still require `review(response.attempt, ...)` after
actual inspection. Changed retained reply bytes cannot be presented or reviewed
as the originally delivered response. Callback completion and acknowledgment
are separate events; neither measures model comprehension or semantic latency.

Both `createRelayClient` and `createInstrumentedRelayClient` check the existing
parent's filesystem capacity before directory allocation, then check the fresh
directory and write `storage-preflight.json` before starting the relay child.
`minimumEvidenceFreeBytes` defaults to 32 MiB and must be a positive safe integer;
choose a larger floor for the expected session evidence. A known shortage throws
`EVIDENCE_CAPACITY`; an unavailable capacity measurement throws
`EVIDENCE_CAPACITY_UNKNOWN`. Neither starts a child or sends an operation. A
failed directory/write check also occurs before child startup. Construction does
not fall back to another filesystem, delete evidence, retry, or launch another
client. An allocated directory left by a failed check remains preserved and
cannot be reused as a fresh session.

The receipt records filesystem-reported availability at that instant and a
successful ordinary write, not reserved capacity or crash durability. It does
not prove quota headroom, WSL virtual-disk physical backing space, or successful
future writes. In particular, free space reported inside Ubuntu does not imply
free space on the Windows drive holding its virtual disk. Check backing storage
separately before a large allocation. Concurrent writers can consume space after
the check; the existing evidence-failure STOP and no-replay reconciliation rules
still apply. The receipt is separate from the per-call host timeline and grants
no input authority or task-success claim. A startup receipt is not an image,
per-call observation, provider-token measurement or benchmark result.

The `text` callback receives both strings and structured objects, including the MCP result-status object. Pass each value to a sink that accepts its type, or format objects explicitly with `JSON.stringify(value)`; do not unconditionally parse callback values as JSON strings. For a sink accepting only text, use `text: async value => deliverText(typeof value === "string" ? value : JSON.stringify(value))`. A callback failure blocks further ordinary calls; reconcile retained replies and close the original transport rather than replaying input.

The callback bodies above must be implemented by the host; empty callbacks do not constitute observation or review. The API does not supply a model, select actions, mint authority, install sensors, queue calls, restart applications or retry input. It returns metadata and the tool's image unchanged. A review receipt records attribution, not proof of perception or semantic completion.

`send` permits one outstanding call. If a host observation times out, await `wait()` on that same client; do not send again or create another client to replay it. Requests and replies are retained before delivery. Files are exclusive writes in a fresh directory; this is not fsync-backed crash durability or authenticated evidence. Ambiguous tool delivery, malformed replies or host-journal errors require reconciliation. `close()` ends the transport only and does not prove application cleanup. Separate caller-owned cleanup may still be needed.

Optional `reuseReviewedImages: true` references only a byte-identical PNG previously delivered and explicitly reviewed within this live host. Current metadata remains separate; identical pixels do not acknowledge task completion. Default false preserves full image delivery. Host timestamps partition transport/presentation/caller intervals; they do not measure isolated model reasoning, useful feedback, actual tokens/cost or human tempo.

Run `node --test runtime/host_v1/test_*.mjs`. The original research modules and frozen evidence remain unchanged; promotion changes only the local import paths. No performance or generic task-quality improvement is claimed.


A program can batch several ordered pointer operations in one dispatch. A drag
uses `pointer_move` to the observed start, `pointer_button` with `down: true`,
`pointer_move` to the observed end, then `pointer_button` with `down: false`.
Focus the configured target in that same program and end with `release_all`.
This is one pointer executing sequentially. Split programs where the next action
requires a fresh visual decision; an `observe` inside a program captures a frame
but does not pause the remaining operations for the model.

[Primary Inkscape batch use](../results/public-inkscape-batch-01/README.md)
records two visually selected drags in one program, a separate save, returned
summary/image reviews, full receipt retrieval without input, and independent SVG
validation. The exact requests are retained as an example, not portable screen
coordinates or default waiting times. No comparison against unbatched use, token
usage or human pace was measured.


For Linux file-spooled host exchanges, the portable runtime also provides
`publish-json --path /absolute/fresh-slot.json --value -` and the Python helper
`runtime.host_v1.file_publication.publish_json`. Supply an already authored JSON
value; no model, input or authority decision is provided. The existing directory
must be caller-owned. The helper writes and fsyncs a private temporary file, then
links the complete bytes exclusively to the final name and syncs the directory.
A reader waiting on that final name cannot see its partial write. Existing slots
are never overwritten. This is the unchanged native-exchange publication
mechanism, exposed for host use.

A post-link failure may leave a complete occupied slot even though the command
returns exit 2. Inspect it and reconcile the original request; do not republish
or replay input after an error/timeout. No filesystem-independent crash guarantee
or producer authentication is implied. Windows/macOS host publication is not
implemented; use this helper inside the Linux/WSL environment. The sequential
stdio relay does not require a file-spooled decision.

[Retained primary six-task use and publication failure/fix](../results/atomic-host-publication-01/README.md) records the incomplete direct comparison and the no-GUI publication checks. The whole integration spine remains unvalidated.

[Primary operation after publication integration](../results/atomic-primary-six-task-01/README.md) completed fresh direct and persistent six-task allocations with separate exact scoring, stale refusal and explicit recovery. It records the remaining timing/acceptance limits.


## Authoring and checking input programs

Before dispatch, validate the same program shapes the caller actually generates,
using `runtime.pyz validate --program /absolute/program.json`. Static validity
checks syntax and expansion; it does not grant runtime admission or freshness.
For pointer input, use `pointer_move` with integer `x` and `y`, followed by
`pointer_button` with `button` and boolean `down`. An observation placed inside
an input program must precede the final `release_all`. Keep the program factory
in a fixed module when the interactive host can retain earlier function bindings;
verify the generated request rather than relying on a helper reassignment.

Inspect the returned image before deciding whether to save or proceed. A completed
dispatch and verified release do not establish application success. If the image
lacks the needed completion cue, request a fresh observation on the same live
session. `interface_results` reads the retained result; it does not wait for the
application to draw a newer frame. Use `include_image: false` when only metadata
is needed, and use the documented `interface_close` before closing the transport.

[Primary public six-task comparison](../results/public-six-task-comparison-04/README.md)
records both routes at 6/6 exact once, changed-layout refusal and explicit recovery,
and a successful submission whose captured image still lacked the final completion
cue. Timing, primary caller failures and unmatched lookup-image accounting remain
scoped; the result does not prove human tempo or token savings.

## Cropped feedback and click coordinates

After inspecting the target layout, an explicit smaller `observe` region can
keep the field, button and completion cue together. For a capture in
`screen_physical_px` with returned region `[left, top, width, height]`, a point
`[u, v]` in the delivered image maps to screen `[left + u, top + v]`. Pointer
operations in `screen_physical_px` still use those screen coordinates. Cropping
does not move the target or change the pointer coordinate frame. This formula
assumes the original image pixel dimensions; account for any host display scaling
before choosing image coordinates. Do not apply a screen origin to a
`window_client` capture; that is a different coordinate frame.

For example, the retained private browser task used region `[10,154,1050,400]`.
Its Save center at image `[365,247]` mapped to screen `[375,401]`. These are
fixture-specific numbers, not reusable target coordinates. Read the current
capture metadata and keep the cues needed for the next decision inside the crop.
A crop excluding the address bar is unsuitable when navigation identity is part
of the task. Widen an observation explicitly when required context is missing.

[Primary full/ROI comparison](../results/primary-roi-feedback-01/README.md)
records correct one-time saves in both fresh sessions and 59% fewer pixels in
the three cropped dispatch captures. The full route needed one explicit requery
because its navigation image was still blank; that timing difference prevents a
causal speed or token-saving claim. Completed input/release does not acknowledge
rendering. Review the returned image before the next input; if it is insufficient,
request a fresh image on the same session rather than replaying the action.

## When input release remains unverified

On the public `persistent-x11` route, `recovery_required=true` blocks further
programs. A synchronized release request is not enough to infer that input is
neutral: a synchronous pointer grab can defer processing of a queued release.
A later read showing an empty button mask does not clear the session's block.
The [retained native discriminator](../results/x11-grab-recovery-01/README.md)
checks this with a separate X connection; it does not identify the cause of every
historical release failure.

Inspect the retained failed receipt and resolve the condition holding input.
Then explicitly call `interface_recover_input` with the open session's current
binding revision. The call only attempts release of tracked inputs. If it returns
`recovery_failed`, keep ordinary input stopped. Do not replay the old program.
The interface does not take over another application's grab or silently retry.

After `input_recovered`, use the returned new binding revision. Request or review
a fresh observation before authoring a new program; the prior program may have
already changed the application. Optional `target` and `region` request a capture
after recovery. An unavailable capture does not undo the completed recovery;
observe separately instead of repeating it. Recovery issues no new lease and
proves neither task success nor redraw completion.

[Primary state-dependent capture](../results/primary-layout-feedback-01/README.md)
records a lower-page form crop followed by a full-frame completion observation.
The saved document cue appeared outside the form crop. Widen capture when the
next action can replace the document or move the required cue. The retained
caller setup failures and expired allocation are included; this single known
task does not establish a general speed or token benefit.

## Authoring deadlines from the live execution clock

For a Windows host dispatching into WSL, call `client.send('interface_clock', {})`
on the same relay client instead of launching WSL/Python again for every clock
sample. Read its text block, verify `schema` and the expected `server_instance_id`,
and use the returned `monotonic_ns` only for an explicitly authorized absolute
expiry. If parsing into JavaScript Number, require safe integers for the sample
and resulting deadline. Clock acquisition adds a sequential MCP call; it does not
issue a lease, select a validity duration, refresh source assertions or recover
input. A caller already inside the execution host can read that host's monotonic
clock directly.

[Clock acquisition and primary use](../results/execution-clock-01/README.md)
retains a fixed local component comparison, startup cost, two fresh known-family
GUI cases, an expired refusal, and failed construction/check results. The shipped
MCP route uses the existing connection; the experimental separate clock process
is not shipped. No whole-task speed, token/cost or human-tempo benefit is claimed.

## Choosing public receipt detail for the next decision

For the public dispatch route, the primary can request the existing summary:

```javascript
const reply = await client.send('interface_dispatch', {
  program,
  current_observation_seq,
  current_binding_revision,
  compact: true,
  report_refs: true,
  detail: 'summary',
});
```

Keep text and image content blocks available to the caller. Eligible completed
dispatches return `agent-interface/receipt-view-dispatch-summary-v1`, an explicit
partial historical receipt. It retains the image, complete capture/release/
activation records, execution outcome, session and raw source digest. Read the
actual image to decide whether the task completed or another action is needed.
The summary's completed execution and verified release do not prove application
success, image readiness, freshness or input authority. Do not decode it as a
complete raw receipt. The default remains full; failed, incomplete, inconsistent
or unfamiliar shapes also remain full.

When a decision needs individual waits, operation history or omitted provenance,
use the returned `presentation.retrieve` instruction. Its
`interface_results` call with `detail: 'full'` and `include_image: false` reads
the retained report without input replay or another image. It does not capture
a newer frame; request a fresh observation on the same session when current
application state is missing. Full retrieval adds a response and round trip.

[Primary full/summary pair](../results/primary-summary-pair-01/README.md)
records the same known-family task at exact once in both fresh sessions, equal
operation shapes and no extra full retrieval. Same-report text was 26.42% smaller
in the summary arm; unchanged image data remains separate. Actual whole-context
model usage is retained with cache and fixed-order limits. Neither that byte
reduction nor the single pair proves lower model cost, faster semantic judgment
or human-comparable live tempo.
## Optional sequential primary caller

[Main packaging and personal use](../results/primary-helper-main-01/README.md)
retains the source-pinned distribution failure, corrected checks, original
six-task candidate evidence, and a fresh exported-helper trial.

The host bundle also exports `createPrimaryCaller` from `primary_caller.mjs`.
This is an explicit trial policy with positional operation helpers. It latches
STOP on unexpected refusals, malformed results, incomplete input, nonneutral
release, transport/presentation failures, or invalid helper arguments. Once
stopped, only `interface_close` may be sent; review/acknowledgment still bind
original retained responses. Choose this policy explicitly for a bounded trial.
The generic instrumented host remains available for caller-decided recovery.

```js
import { createPrimaryCaller } from './host-bundle/primary_caller.mjs';
const primary = createPrimaryCaller(client, 'guarded-local', sinks, [], {
  reviewWindowId: explicitlyConfiguredWindowId,
});
const observed = await primary.observe();
// Actually inspect the image, then record the returned attempt's review.
await primary.review(observed.attempt, { task, phase: 'observe', reason });
const minted = await primary.mint(alias, sourceSequence, point, regionSize);
await primary.acknowledgeText(minted.attempt, {
  task, phase: 'mint', reason: 'Read this original mint response',
});
const acted = await primary.input(alias, offset, 'click', explicitTail);
// Review the acted image before the next decision. Do not infer task success
// from neutral execution alone. Close the public session before the host.
const closed = await primary.call('interface_close', {});
await primary.acknowledgeText(closed.attempt, {
  task, phase: 'close', reason: 'Read the original close outcome',
});
await client.close();
```

`mint` requires four positional arguments and `input` requires alias, explicit
offset, interaction and tail. `reviewWindow()` uses its configured window ID;
guarded `observe()` accepts no per-call scope. Direct-route observation uses
the constructor's explicit snapshotted observation arguments. Image reviews and
text acknowledgments require `response.attempt`, not the entire response object.
Exact one-use declared refusal controls are optional trial configuration. They
do not authorize retries, refresh evidence, infer targets, select actions or
prove semantic completion. This wrapper's tool allowlist excludes activation;
the generic host exposes the separately documented activation/recovery route.
# Optional feedback after public input release

The `persistent-x11` public MCP route accepts `inspect_after: "app"` with
`inspect_after_region: [0, 0, 1280, 800]`. It captures that explicit physical
screen region after completed input and verified neutral release, and rechecks
focused-target metadata. The default adds no capture. Inspection never selects
a target, advances binding or grants input authority.

A program can omit its inline `observe` when this later image is the intended
feedback. If both exist, both are retained; an eligible later capture is selected
for delivery. Its reference names `post_dispatch_observation_id` and
`capture_phase: "after_dispatch_release"`. Capture failure or changed target
retains the original execution result and any inline image. Never replay input
to recover a receipt or image.

`inspect_after_wait_ms` optionally requests a 0–1000ms sleep after verified
release and before capture. It requires a region and records `capture_wait`
with `update_observed: null`. This is a fixed delay, not redraw detection or
semantic completion. Retained-result lookup neither sleeps nor recaptures.

For an eligible no-inline-observe post-release result, request `compact: true`,
`report_refs: true`, `detail: "summary"`. The server uses its pre-invocation
program copy to validate completed-operation and wait counts. The summary
labels this separate invocation provenance; the report digest identifies the
raw report. Full lookup retains `retained_call.arguments.program`. Unknown,
failed or inconsistent shapes retain full feedback. CLI summaries do not have
this server invocation context.

The [current-main real Calc trial](../results/calc-main-entry-01/README.md)
demonstrates why completed input and a later metadata sample do not establish
that the captured image contains the completion cue. Read the actual image and
request another observation when needed. Optional availability is not evidence
of general speed, human tempo, token savings or a completed six-task integration.
