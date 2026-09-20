# Using the current interface

The current Linux/X11 interface supports explicit actions, referenced images and
bounded continuation. It remains a research preview. The primary model chooses
the action; these entry points do not require a second model or a subagent.

## Choose an entry point

| Entry point | Use | Lifecycle |
|---|---|---|
| [Public CLI/API](cli_v1/README.md) | Existing target mappings and admitted programs; ordinary application integration | One-shot dispatch/observation |
| [Native MCP adapter](../research/live_control/NATIVE_MCP.md) | Existing private native harness, or one explicitly managed allocation | Bound run, explicit stages and exact-request resume |
| [Local integration checks](integration_checks/README.md) | Verify the implementation without GUI or model calls | Fresh output directory with logs |

An MCP host must launch the configured stdio server and forward its image blocks.
Adding configuration does not prove tools are available in a running host. The
public CLI emits JSON; an assistant integration must render its image payload.
Neither route establishes end-to-end latency merely by returning an image.

## Public actions and images

From the repository root, inspect the installed command surface:

```sh
python3 -m runtime.cli_v1 --help
python3 -m runtime.cli_v1 observe --help
python3 -m runtime.cli_v1 dispatch --help
```

For X11 `observe` or `dispatch`, add `--capture-directory` and `--review` to return
a review envelope in the same invocation. Supply your actual target mapping and
program using the public CLI guide. For dispatch, the envelope selects the last
recorded capture in execution order; operations after it may have changed the
screen. A failed or missing latest capture does not fall back to an earlier one.
A valid image is not proof that an action or task succeeded: inspect the outcome,
execution error and cleanup information alongside it.

For an already saved report, review is read-only:

```sh
python3 -m runtime.cli_v1 review --report /absolute/run/report.json --run-directory /absolute/run
```

Add `--compact` to this read-only command to replace duplicate event objects with
local references. It also accepts `--report -` for a complete response on stdin.
The image, outcome summary and source digest are preserved. Consumers can use
`runtime.cli_v1.receipt_references.expand_receipt` to reconstruct the original
receipt view; only the explicitly listed reference paths are interpreted.
This optional representation can add overhead to small receipts and has no
measured model-token or cost benefit. The default representation is unchanged.

The report and referenced image must be present at their recorded paths. The
review operation does not recapture, focus a window or repeat an action. Native
research reports use `agent_review.py --native` as described in the MCP guide.

## Native decision loop

1. Start one explicitly managed allocation, or attach to an existing run. Read
   its goal and initial image using `native_observe(stage=1)`.
2. Choose a decision from that image and submit its exact `source_sequence`.
   Click/keyboard actions need their observed point and expected title.
3. If the result is pending, retain the stage and `decision_sha256`; call
   `native_resume` with those same values. Do not submit the action again.
4. Inspect the returned image and action outcome. `continuation.source_available`
   supplies the next stage/source only when retained source and image identity
   agree. It is descriptive, not permission to skip normal admission checks.
5. To inspect a freshly painted screen, submit only `source_sequence` and
   `interaction: "observe"`. This consumes a stage and sends no input.
   `native_observe(stage)` instead reads an already retained source.
6. Finish with only `source_sequence` and `finish: true`, or explicitly use
   `finish_after: true` on an action when no further decision is needed.

A typed target refusal can return a new image while stage capacity remains. Read
`target_refusal` and choose a new decision; the refused action is not replayed.
At capacity exhaustion, the terminal `needs_review` reply retains the final
observation and cleanup result, and publishes no unusable next source. Process
exit, action completion, cleanup and task evaluation are separate facts.

When recorded verification flags exist, `outcome_summary.cleanup_verification`
projects `tracked_processes_terminal`, `owner_exit_verified` and
`descendants_verified` separately. A `cleanup_status` of `completed` only says the
cleanup routine completed; it does not establish that every descendant exited.
Only explicit booleans are projected; missing or malformed flags are `null`.
The original cleanup receipt is preserved. The managed `allocation` object is a
process snapshot: its `task_success: null` does not override a recorded
`evaluation_success: true`, and a zero process exit code does not prove task success.

## Validate an integration

Follow [the shared check instructions](integration_checks/README.md) for a single
Python environment or split WSL environments. Use a fresh output directory:

```sh
python3 runtime/integration_checks/native.py --output results-local/native-check-01
```

The report includes suite exit codes and hashes of complete logs. The Native MCP
workflow uses this same runner. Broker/bridge contracts have a separate check:

```sh
python3 -m unittest runtime.test_host_model_ipc_broker_v1 runtime.test_docker_host_model_bridge_v1
```

These checks do not start an application or model. Passing them does not establish
human-tempo operation, cross-application reliability, token/cost reduction or
current-model compatibility. Frozen experiments remain evidence for their pinned
sources; integration commits do not extend those claims to a newer build.
