# Standard-caller Xvfb raw re-score — r09

This additive packet retains the already completed [Runtime X11 v1 Integration run 39276306835](https://github.com/Unjuno/agent-interface/actions/runs/39276306835), PR head `f4e02b64f0d324ffa8c3525a9f822691c1e06fa4` (merged PR [#9198](https://github.com/Unjuno/agent-interface/pull/9198)). The workflow and every retained raw artifact are from that run. The raw outcomes in r01–r08 remain untouched. These bytes were downloaded from the GitHub run artifacts; this packet does not rerun the experiment.

The run used private Xvfb `2:21.1.12-1ubuntu1.8` (binary SHA-256 `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`), the standard MCP caller, a synthetic application, and an injected delayed request. The workflow checkout was merge commit `82d005ab2a8a1a9eaf2eb18bbe74afb5074701cd`, with PR head `f4e02b64f0d324ffa8c3525a9f822691c1e06fa4` as its second parent. It retained one withheld-cancel-ack case and four A-B-B-A owner-method-tracing comparisons. Each report records the owner blocked in `python-xlib Display.sync`, the exact owner process, XRes disconnect observation, separate release worker, independent parent keymap readback, and the delayed-request horizon. The delayed action was scheduled at 8,000 ms; the independent horizon readback was around 8,500 ms after cancel.

After PR #9200 merged the independent synthetic-task scorer, `rescore.py` applied that scorer to the preserved effects and readbacks. All five receipts independently score the defined synthetic task PASS: the observed app property was exactly `[1]` before cancellation and remained `[1]`, `a` and `b` were both up at separate-client release readback, and both remained up at the late-request horizon. A negative control with `a` still down at the horizon scores FAIL. `offline-rescore.json` retains per-run source hashes, timing, and score checks.

The same successful workflow also retained `standard-mcp-xvfb-generation.json`: its separate generation-and-recovery scenario reports `PASS_SCOPED_XVFB_STANDARD_CALLER_RECOVERY`, carries process and window generation digests through the standard MCP path, refuses stale generations, and records an independently observed post-recovery synthetic effect `[3]` with a press/release pair. That is a separate test scenario in the same workflow, not a combined cancellation-plus-recovery trial; its runtime task-success API is also null.

The generation report also qualifies timing endpoints for that separate scenario: observe call start-to-return was 594.581 ms; after an injected release failure, the explicit recovery call through independent key-up readback took 5.016 ms against a 3,000 ms test bound; the fresh post-recovery input reached its independent synthetic effect in 52.432 ms. These are one-run component timings, not model latency or an efficiency comparison. `offline-rescore.json` carries the timestamps, endpoint labels, raw SHA-256, and generation digests.

This post-hoc PASS is scoped to the synthetic task oracle. The original cancellation runtime results remain unchanged: `task_success=null`, `release_confirmed=false`, `cleanup_status=UNKNOWN`, `late_server_request_possible=true`, and replay denied. The trace shows this Xvfb schedule completed bounded caller cancellation and an independently observed release; the separate generation scenario shows one bounded recovery followed by a fresh task effect. Neither establishes a server-wide outage bound or universal X11 queue ordering. Five cancellation runs in one CI job are not a reliability estimate. Matched efficiency remains unmeasured.

| Receipt | Trace mode | Cancel return (ms) | Separate release worker (ms) | Runtime result | Independent task oracle |
|---|---:|---:|---:|---|---|
| withheld-ack baseline | traced | 912.121 | 582.074 | `cancel_unconfirmed`, cleanup UNKNOWN | PASS |
| no-trace-1 | off | 653.306 | 572.423 | `cancel_requested`, cleanup UNKNOWN | PASS |
| trace-1 | on | 666.996 | 587.921 | `cancel_requested`, cleanup UNKNOWN | PASS |
| trace-2 | on | 689.328 | 609.617 | `cancel_requested`, cleanup UNKNOWN | PASS |
| no-trace-2 | off | 673.388 | 592.997 | `cancel_requested`, cleanup UNKNOWN | PASS |

Reproduce from the repository root with `python research/integration/standard_caller_xvfb_cancel_trace_20261019/r09/rescore.py`. The only code it imports is the merged test-only scorer. Do not replace these original artifact outcomes with the rescore.
