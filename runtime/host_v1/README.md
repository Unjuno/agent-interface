# Sequential relay host API

These Node.js ES modules expose the already exercised relay client, optional host instrumentation and primary caller policy outside the research tree. They use only Node built-ins and launch an explicit command supplied by the caller. Copy `relay_client.mjs` and `relay_host.mjs` together to use them outside a checkout; include `primary_caller.mjs` when using the opt-in policy. The optional portable host bundle contains all three. They are separate host files, not Python zipapp entries, and require Node.js 22 or newer. The execution relay can be the portable Python archive; see [public MCP transport](../cli_v1/MCP.md).

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

For a call that must be delivered before the caller handles its outcome, use the opt-in composed method:

```js
const response = await client.sendPresented('interface_guarded_input', args, {
  text: deliverText,
  image: deliverImage,
});
// Both callbacks have completed. Now inspect the unchanged typed outcome.
// isError may carry a refusal; it is not automatic permission to retry or recover.
```

This uses the same retained send/present path, snapshots and validates both callbacks before dispatch, and reserves the host until presentation finishes. Another send, review or close during that interval is refused rather than queued. If interrupted, await `client.wait()` on the same host: it returns the original combined promise. Rendering failure leaves the reply retained, blocks further input and permits transport cleanup. A successful callback is delivery only; explicit review, outcome interpretation, release validation and any bounded recovery remain caller responsibilities. Existing separate `send`/`present` behavior is unchanged.

The host creates `evidenceDirectory` exclusively. Supply a path that does not exist; do not create that directory before constructing the client. Keep the returned client in a durable caller binding before starting subsequent presentation work.

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

For a returned response containing only text, use a separate acknowledgment after
delivering and reading the original text:

```js
await client.acknowledgeText(response.attempt, {
  task: 'edit', phase: 'refusal', reason: 'Describe the original text read',
});
```

This requires completed presentation callbacks for that exact retained reply
digest. It rejects unpresented or changed replies, empty content, images and
non-text content. It preserves an explicit `isError` flag and writes an exclusive
`text-acknowledgment-N.json` plus a `text_acknowledgment_recorded` host event.
This is caller attribution to original text, not an image review or proof of
comprehension, task success, safe input or permission to retry. `review` still
requires its original sourced report and image. Neither acknowledgment method
dispatches another tool call. Missing attribution arguments are rejected before
starting a host operation; evidence failures block ordinary calls while leaving
transport cleanup available. Original replies and existing receipts stay intact.

The `text` callback receives both strings and structured objects, including the MCP result-status object. Pass each value to a sink that accepts its type, or format objects explicitly with `JSON.stringify(value)`; do not unconditionally parse callback values as JSON strings. For a sink accepting only text, use `text: async value => deliverText(typeof value === "string" ? value : JSON.stringify(value))`. A callback failure blocks further ordinary calls; reconcile retained replies and close the original transport rather than replaying input.

A returned MCP reply may have `result.isError: true` while carrying a typed refusal and its critical image. Present and retain that reply before raising a caller exception; keep its attempt and reply identity available for reconciliation. Do not treat every error flag as uncertain input, or treat a refusal as permission to retry. Inspect the typed outcome, input-dispatched flag, completed effects and release state. Any read-only target review and re-grounding must follow an explicit bounded caller decision; partial/unknown delivery must not enter the normal field→Save continuation. [The guarded/direct six-task comparison](../results/post-release-spine-02/README.md) records a caller that lost this presentation step and required primary intervention.

The callback bodies above must be implemented by the host; empty callbacks do not constitute observation or review. The API does not supply a model, select actions, mint authority, install sensors, queue calls, restart applications or retry input. It returns metadata and the tool's image unchanged. A review receipt records attribution, not proof of perception or semantic completion.

`send` permits one outstanding call. If a host observation times out, await `wait()` on that same client; do not send again or create another client to replay it. Requests and replies are retained before delivery. Files are exclusive writes in a fresh directory; this is not fsync-backed crash durability or authenticated evidence. Ambiguous tool delivery, malformed replies or host-journal errors require reconciliation. `close()` ends the transport only and does not prove application cleanup. Separate caller-owned cleanup may still be needed.

Optional `reuseReviewedImages: true` references only a byte-identical PNG previously delivered and explicitly reviewed within this live host. Current metadata remains separate; identical pixels do not acknowledge task completion. Default false preserves full image delivery. Host timestamps partition transport/presentation/caller intervals; they do not measure isolated model reasoning, useful feedback, actual tokens/cost or human tempo.

Run `node --test runtime/host_v1/test_*.mjs`. The original research modules and frozen evidence remain unchanged. The optional primary policy and its regressions are described below. No performance or generic task-quality improvement is claimed.

## Optional primary caller policy

`primary_caller.mjs` exposes the policy used in the primary integration trials
as `createPrimaryCaller`. It composes an instrumented host and the same delivery
callbacks, checks the selected mode's tool set and guarded interaction enum,
and latches STOP on unexpected refusals, uncertain transport/presentation,
incomplete input, nonneutral release, or response extraction/validation failure.
A caught extraction exception cannot authorize a second ordinary call. The
original exception propagates after STOP is set; the host has already presented
and retained the original response. To reconcile a retained response, use the
same host's `wait()`; never resubmit the input. Caller STOP permits only
`interface_close` tool calls, plus attribution and host transport cleanup.
Public close still requires the primary to inspect its release/cleanup outcome.

```js
import { createPrimaryCaller } from './primary_caller.mjs';
const primary = createPrimaryCaller(client, 'guarded-local', {
  text: deliverText, image: deliverImage,
});
const frame = await primary.observe(); // same helper for initial/fresh grounding
// Actually view the original delivered image, then record that exact attempt:
await primary.review(frame.attempt, {
  task: 'edit', phase: 'observe', reason: 'Describe the image actually viewed',
});
// Choose a unique alias and a point from that reviewed image:
const reference = await primary.mint('save_fresh', sourceSequence,
  [376, 401], [24, 38]);
// Read the original mint response, then explicitly choose actions with call(...).
```

`observe()` accepts no per-call arguments and sends `interface_guarded_observe`
with `{}` in `guarded-local` mode. It does not mint or renew a reference, choose
a target, check expiry, retry input, or claim the primary saw the frame. For
`direct-post` mode provide the target/frame/region explicitly once:

```js
const primary = createPrimaryCaller(client, 'direct-post', sinks, [], {
  observationArguments: {
    target: 'editor', frame: 'screen_physical_px', region: [0, 0, 800, 600],
  },
});
```

`mint(alias, sourceSequence, point, regionSize)` is an explicit guarded-only
helper. It sends exactly `interface_guarded_mint` with `source_sequence` and
`region_size`, preserving the original response and STOP behavior. It requires
four arguments, a nonempty alias, a positive safe integer source sequence,
integer point coordinates, and two integer region dimensions in 4..96.
Malformed helper arguments latch STOP before host dispatch. It does not select
coordinates, observe, review an image, renew a reference automatically, retry,
or issue input. Alias admissibility, image binding, freshness and geometry are
still checked by the server. Use `call` for exact preregistered refusal controls.

The settings are snapshotted; later caller mutation does not change observation
scope. Missing direct observation configuration or accidental helper arguments
latch STOP locally. `call`, `review`, `acknowledgeText` and `state` remain
explicit methods. Input authority, geometry, source binding, leases and runtime
admission remain separate server responsibilities. This wrapper does not enforce
semantic correctness or attest image comprehension.

The fourth argument optionally supplies exact, one-use expected-refusal controls
for preregistered experiments; normal use should leave it empty. Only the
declared matching no-input refusal may leave this policy running. It grants no
runtime authority and never changes the delivered `isError`, text or image.
Ordinary non-error response metadata must contain a JSON object; malformed
metadata causes STOP rather than silently becoming an untyped success.
Unexpected MCP errors may contain free text: the original response is returned
unchanged after STOP is latched. Frozen spine07/08
callers and their failures are unchanged. Regression tests address the reported
malformed-envelope gap and the spine08 observation mistake; they do not establish
a new completed GUI comparison, real transport uncertainty or speedup.


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

## Capturing after verified input release

On the public `persistent-x11` dispatch route, request `inspect_after: target`
and `inspect_after_region: [left, top, width, height]` to capture once after
completed input and verified neutral release. The region uses
`screen_physical_px`; it must be valid before input begins. Target focus metadata
is checked before and after capture. This extends the existing optional
post-dispatch inspection and does not select a new target or advance binding.

A program may omit its inline `observe` when this later image is the intended
feedback. If it contains both, both captures are retained, and an eligible later
image is selected for delivery. Read `image_reference.post_dispatch_observation_id`
and `capture_phase: 'after_dispatch_release'` to distinguish it from an inline
execution observation. The complete later observation stays in
`post_dispatch_inspection.observation_report`. Failure, refusal, recovery-required
state or unverified release skips the later capture. Capture/target-check failure
keeps the original input result and any original inline image.

Optional `inspect_after_wait_ms` (an integer from 0 to 1000, requiring a region)
adds an explicit sleep after verified release and before inspection/capture.
The default adds no wait. `post_dispatch_inspection.capture_wait` retains its
requested duration, start/end, completed flag and `update_observed: null`. This
sleep does not detect redraw, extend the input lease or grant input authority.
Refused input, recovery and unverified release skip both wait and capture.

A no-wait held-button experiment completed Save exactly once but still required
a fresh observation: its captured frame lacked the saved cue and the metadata
changed during capture. Capture ordering alone is insufficient; application
settling and the extra receipt cost must be evaluated on actual tasks.

This is a read-only capture, with no redraw detection, semantic
success inference or input replay. A later frame can still lack the completion
cue. Inspect the actual image before deciding the next action; request a fresh
observation when necessary. Historical `interface_results` returns the retained
selection without recapturing or renewing the target review request. Full
receipt fallback remains available when summary eligibility is not met.

The [retained integration candidate](../results/post-release-feedback-01/README.md)
includes ordinary and held-input failures, the explicit-wait pair, receipt-size
cost and independent exact-once scoring. Its task-4 scope does not establish
the full six-task integration spine or human-comparable tempo.

For a successful public post-release capture without an inline observe,
`detail: summary` can use the server's pre-invocation program copy to check
completed operation and wait counts. It leaves the complete inspection and
image reference visible. The report digest identifies the raw report; this
separate invocation context is labelled in `presentation.program_provenance`.
Full `interface_results` includes the original program in
`retained_call.arguments.program`, without replay or a new capture. Missing or
inconsistent invocation/capture evidence and failed/unknown wait shapes stay
full. CLI summaries have no server invocation context and retain their existing
full fallback when raw provenance is absent.

The [retained real-X11 send/presentation smoke](../results/host-presented-send-01/README.md) exercises typed refusal delivery before the composed promise resolves, an explicit read-only binding review, and neutral close. It addresses the prior caller presentation loss; it is not an automatic recovery or six-task integration pass.
