# Codex app-server planner cancellation path

The v24 live result exposed four model calls that became stale but still ran to
completion.  Killing the current Python `subprocess.run` wrapper is not a sound
repair: the wrapper owns a Node process, Node owns the native Codex process,
and forced outer termination does not provide an interrupted turn record or
complete partial accounting.

Codex app-server provides the required lifecycle directly.  Its documented
`turn/interrupt` request accepts `threadId` and `turnId`; completion is reported
as `turn/completed` with status `interrupted`, and token usage is emitted through
`thread/tokenUsage/updated`.  `turn/start` accepts local image input, model,
effort, and output schema, so it can replace the one-shot CLI bridge without
weakening the structured planner contract.  Primary references are the
[official app-server protocol](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
and [official Python client](https://github.com/openai/codex/blob/main/sdk/python/src/openai_codex/client.py).

`codex_app_server_client_v1.py` implements only the required synchronous JSONL
transport: one reader thread routes responses and notifications, request writes
are serialized, and another controller thread may call `turn/interrupt` while a
planner thread waits for `turn/completed`.  Interrupted status is evidence of
no answer; it must never be parsed or admitted as an action.

A command-free probe against local `codex-cli 0.153.4` initialized the server,
listed six models, found Luna, and created a read-only ephemeral thread without
starting a model turn.  It also retained a compatibility defect: generated
`ThreadStartParams.ts` types `sandbox` as `SandboxPolicy`, but the corresponding
map was rejected with JSON-RPC `-32600`; the legacy `"read-only"` thread string
was accepted and returned the resolved policy.  The exact failed source and
generated type are retained beside the corrected probe.  This is transport
evidence only.

The next test must be separately frozen before `turn/start`.  It should start
one bounded no-tool turn, wait for its returned turn ID, send one interrupt,
require the interrupt acknowledgment and `turn/completed(status=interrupted)`,
retain the latest per-turn usage if emitted, verify no completed agent message
is treated as an answer, and close the app-server cleanly.  A race in which the
turn completes before interrupt is a retained outcome, not a retry trigger.
