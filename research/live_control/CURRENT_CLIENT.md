## Fixed-task profiling finds material journal cost; location alone insufficient

Actual Inkscape ABBA received/durable,32 calls: outside-transport median0.165/0.255ms for received clock/observe vs33.605/35.812ms durable. Same durable API ABBA mounted/native adds32 calls; native residual31.246/31.204ms, session totals overlap mounted, location-only improvement not established. Both audits64 calls/eight clean runtimes/40 exact frames/unchanged SVG pass. Static store cProfile shows native fsync about92% of store time; mounted cost spread over filesystem operations. See research/live_control/CALLER_COST.md. Static observe task, no model/equal crash guarantee/general speed claim. Next reduce repeated directory persistence via bounded journal candidate while retaining pre-send uncertainty; verify recovery before performance promotion and model-facing use.

## Journal-owned clock closes rejection-to-new-action path on actual GUI

Durable v3 persists clock uncertainty and correlates exact echo/clock while retaining image evidence. Inkscape seed235: expired X96 request/process exit, rejection read-only recovery, then journal clock→fresh observe→clock→distinct X104/save. Audit62 events/10 exact frames/three accepted released programs/one rejected with zero started steps, own-clock sequences/deadlines and SVG104,50,40,30/no transform; same bridge live/final exit0/socket cleanup. Five injected clock replies verify orphan/echo/timeout/malformed remain unresolved and two new commands blocked, own valid clock resolves. See research/live_control/DURABLE_REPLAN.md. Scripted plan, no new model/human speed claim. Next fixed-task caller overhead measurement and real model-facing use, not more isolated recovery variants.

## Identified rejection now reconciles real expired request after caller exit

Runtime candidate tags submit rejection with action/request identity and not_admitted only before executor used-ID admission. Journal v2 matches exact echo/identity and refuses resolution after acceptance. First actual attempt retained: legacy scope labeled rejection unattributed and recovery exited1/pending retained. Scope/cursor/socket v2 fixes explicit identity matching; second actual Inkscape attempt recovers in one command-free read, three workers17/0/0, same bridge live, final exit0. Audit21 events/three exact frames, no expired edit admission/steps, SVG unchanged50,50,40,30. Nine control groups/previous terminal compatibility pass. See research/live_control/ATTRIBUTED_REJECTION.md. Next journal-owned clock/observation and fresh distinct action after rejection; no speed/default promotion.

## Durable journal now recovers actual GUI command across caller process exit

Inkscape seed233: worker sends real AF_UNIX edit/save then os._exit17 before recv; another worker is refused before transport; third worker performs one command-free read and reconciles exact echo/admission/released terminal on same live bridge. Audit49 events, nine exact frames, three worker PIDs, unique edit/save, SVG96,50,40,30/no transform; finish/bridge exit0, sockets removed. Send-to-recovery-worker exit852.547ms, single scripted case including startup and application work, no model/human-speed claim. See research/live_control/DURABLE_INKSCAPE.md. Next attributable rejected outcomes; no automatic resend or timeout-based uncertainty reset.

## Pending submit identity survives caller process loss

Linux durable_submit_v1 commits uncertainty before transport and serializes cooperating callers with flock. Five separate worker invocations verify crash exit17, two new-submit refusals before transport, admission remaining pending and correlated released terminal resolution. Four attribution/release controls and cross-process lock contention pass. Recovery uses injected archived Inkscape replies with rebound identities; no new live GUI/network or power-loss claim. See research/live_control/DURABLE_SUBMIT.md. Next real write/crash/resume on the same live runtime; rejected events currently lack identity and conservatively remain pending.

Actual checkpoint caller recovery: [Inkscape response abandonment](INKSCAPE_LOST_REPLY.md). One edit/save is recovered by reading from prior cursor; no resend. Scripted GUI test, not a general failure supervisor.

Real transport continuation test: [split clock response over private socket](SPLIT_CLOCK_SOCKET.md). One clock request survives old response and pending timeout; synthetic runtime, not GUI/model performance.

Continuation candidate: [retained images, received cursors and request-correlated clocks](RECEIVED_CONTINUATION.md). Archive replay and injected transport tests only; use v2 wrapper for pre-send session validation.

Actual shared-contract desktop use: [Inkscape guarded click and cursor recovery](INKSCAPE_GUARDED_CLICK.md). One saved edit succeeds; rendering mismatch and stale-clock caller failure are retained. Experimental only.

Experimental target revalidation: [shared sampled-target contract](SAMPLED_TARGET_CONTRACT.md) separates per-app patch/point declarations from checks; four archived cross-domain cases, not yet wired as a default caller.

# Current Linux research client: entry point and limits

These versioned candidates are research tools used in private Linux/X11 fixtures.
They are not a released desktop product or a promotion of the frozen architecture.
Keep the older sources/results: versions name measured implementations.

The [v2 prepared checkpoint caller](CHECKPOINT_CONTINUATION.md) distinguishes valid
UNKNOWN/busy evidence from inconsistent replies before writing continuation data.
Its policy and mocked wrapper controls pass; actual GUI self-use evidence below
still belongs to v1. Both remain optional.

[prepared_checkpoint.py](PREPARED_CHECKPOINT_SELF_USE.md) now combines an explicit
program, saved-contract checkpoint and opt-in conditional finish. Actual Calc
use returns the modal for a decision, then independently finishes in the second
call. It remains optional and requires runtime v31/socket v16; do not infer a
general completion policy from this known task.

An optional [explicit checkpoint-then-finish policy](CHECKPOINT_FINISH.md) uses
checkpoint_finish.py with runtime v31/socket v16. It leaves UNKNOWN open and sends
scoped final evaluation only for a caller-selected matching saved-artifact contract.
This has scripted Calc evidence, not actual assistant or general completion-policy
validation. It is separate from the default stack below.

For checkpoint evidence that must be re-parsed after the source changes, optional
[runtime v30/socket v15](CHECKPOINT_ARCHIVE.md) archives the sampled bytes. A scripted
Calc run replays both pre-save and saved states after source cleanup. Archiving
adds storage/I/O work and has not repeated cancellation tests; it is not a default.

An optional [non-final artifact checkpoint](EFFECT_CHECKPOINT.md) candidate uses
runtime v29/socket v14. It can sample saved fields while leaving admission open;
its scoped VERIFIED evidence is separate from task success. Browser integration
is scripted. [Actual Calc checkpoint use](CHECKPOINT_CALC_SELF_USE.md) now verifies
the specified saved cells before/after format confirmation. CPU/output contention
during cancellation remains untested. It does not replace the default stack below.

A [sleeping-verifier cancellation control](CHECKPOINT_CANCEL.md) now confirms
matched cancellation and verified release before the verifier gate opens in one
live run. CPU/GIL and blocked-output contention remain untested.

Optional [client endpoint instrumentation](CLIENT_ENDPOINTS.md) in
prepared_exchange_v6.py separates preparation, persistence, response receipt,
decoding, image/result processing and stdout completion. It remains a candidate;
model timestamps and live instrumentation overhead are unmeasured.

| Component | Current candidate | Purpose |
|---|---|---|
| Runtime | interactive_v27.py | bounded programs, input ownership/release, observation evidence and retained finalization |
| Transport | event_socket_v11.py / event_cursor_v5.py | private Unix send/wait, request identity, retained record prefixes |
| Preparation | prepare_program.py | explicit steps plus received observation/delivery/time fields |
| Caller | prepared_exchange_v4.py | prepare, persist exact request, send, wait, save full reply and select image |
| Result-only caller | outcome_client.py | wait for early/final result, bounded status fallback after timeout |
| Optional final drain | drain_final.py / unix_json_deadline.py | one read for an already available final result, 250 ms optional I/O budget |

## A configured research session

From the repository root in the existing Linux research environment, start:

```sh
python3 -u research/live_control/event_socket_v11.py serve -- \
  --app calc --seed 991031 --out research/live_control/results-local/my-run \
  --presentation compact
```

Use the emitted socket path, not a path copied from a previous session. Runtime
output paths must be new. First acquire an observation and clock with the existing
socket read command and persist that complete batch. Inspect the referenced image.
Choose explicit steps; do not infer task success from input acceptance.

For this WSL-hosted setup, the [combined report/image recipe](COMBINED_IMAGE_SELF_USE.md)
can display the validated referenced image in the same outer tool response as the
received records. It avoids a display-only model turn without choosing the next
action automatically. The recipe preserves records and uses original image detail.

prepared_exchange_v4 takes SOCKET, BATCH, RUN_DIRECTORY, PROGRAM_ID, STEPS_FILE,
--lease-ms, --boundary terminal|outcome and --out NEW_ARTIFACT_DIRECTORY.
Use terminal when another visual decision is required; outcome reserves the final
program and closes admission after it ends. --producer scripted distinguishes
automated probes; actual assistant use defaults to assistant. Attribution is
caller-declared, not proof of viewing.

[The confirmation boundary comparison](CONFIRMATION_BOUNDARY.md) demonstrates
the practical difference: outcome on the first submission closes admission before
a required confirmation can run, while terminal review permits that additional
program. Outcome is a finalization request, not an admission-preserving effect
query. Terminal completion itself provides no independent task-success verdict.

--drain-final is optional. On early effect evidence, it tries one final-only read
without server event waiting. A ready final evaluation can return within the same
caller invocation; otherwise scoped early evidence and a continuation remain.
Direct final evaluation skips the drain. Use report records/cursor and saved raw
batches together; do not discard intervening interrupts. Image selection does not
refresh observation. Leases use historical time, and runtime admission may reject
an old request. No caller may turn metadata into fresh authority.

## Evidence and unresolved behavior

Optional timing instrumentation is a separate candidate: interactive_v28,
event_socket_v12 and prepared_exchange_v5 record explicit Linux clock identity.
[Clock identity evidence](TIMING_CLOCK.md) covers one scripted Calc integration;
model timestamps and live instrumentation overhead remain unmeasured.

[Local metadata cost audit](CLOCK_METADATA_COST.md) now measures raw JSON byte
and serialization overhead only. A lossless shared-domain batch codec is offline;
live critical-path overhead and actual model tokens are still unmeasured.

| Path | Evidence |
|---|---|
| Ready Calc early + final, same caller | [actual assistant use](DRAIN_FINAL_SELF_USE.md), 13 exact frames |
| Delayed final evaluation | [integrated scripted gate test](LIVE_DRAIN_DELAY.md), returns early then resumes |
| Drain socket stall, trickle, malformed/truncated/oversized reply | [real private socket controls](DRAIN_SOCKET_DEADLINE.md), prior evidence preserved |
| Browser direct final, no redundant drain | [actual assistant use](DRAIN_BROWSER_SELF_USE.md), 13 exact frames |
| Evaluator exception and status query identity | [live status correlation](STATUS_CORRELATION.md), bounded [caller fallback](OUTCOME_FALLBACK.md) |

The initial send/wait still has a 35-second socket timeout; only optional drain
I/O has the short absolute budget. File writing, parsing and scheduling are not
hard wall-time bounded. Transport errors must not cause a fresh input replay.
Requests are persisted before send, but files are not a durable exactly-once
journal. Cursor/request identity is session-local, not restart-safe. Outcome mode
cannot reopen admission for a post-finalization correction.

Measured outer decision intervals still take seconds. Same-call collection can
remove a caller boundary, but matched causal speedup, actual model tokens/cost,
human comparison, complete clock envelopes and cross-domain freeze criteria are
not established. No Windows/macOS product support is implied. DOOM remains one
orthogonal motor stress benchmark, not the definition of interface success.
