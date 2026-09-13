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
