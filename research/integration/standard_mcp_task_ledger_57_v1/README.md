# Standard MCP task ledger v1 — offline contract check

Status: local measurement-infrastructure construction only. This does not run a
model, GUI, WSLc, Docker, or a formal allocation, and does not qualify the
integrated route.

The earlier retained [r01 packet](composition-evidence-20261020/README.md)
captures the immediate-response stale-generation case. The follow-up
[r02 packet](composition-evidence-20261020-r02/README.md) holds the fake
provider response, changes target generation while it is waiting, then confirms
the standard public caller refuses before input. Its event journal orders the
fake provider completion before the tool call. Both are synthetic composition
evidence only; neither establishes a live model, physical release,
blocked-I/O recovery, or matched efficiency.

The [current-main R03 local recheck](current-main-20261022-r03-local-recheck/README.md)
revalidates the supervisor/owned-caller/server-stop suite (63 tests, one
skipped) and this ledger/provider-recorder/public-MCP suite (33 tests) in
normal and optimized Python at commit `1263068a`. It includes the fake-provider
target-generation refusal through the public compiled endpoint. The packet
retains exact commands, raw output, exits, conditions and source blob IDs.
This is still injected-provider contract evidence. It establishes neither a
production provider adapter nor external usage reconciliation, live GUI
effect, shared-desktop release, WSLc, matched efficiency, or reliability.

## Question and use

Issue #57's current public `interface_guarded_compiled` caller lacks one joined
record for provider attempts, MCP calls, and an independent application score.
The current owner timing receipt covers only `run_compiled` after the call root
exists. This packet adds a small validator for a future one-task comparison
record so every returned, failed, timed-out, refused, malformed, and abstained
model attempt can be represented alongside the fixed route and raw evidence.

Each record pins comparison arm/block/order/seed, task fixture and scorer
digests, source commit and route digest, environment digest, model/effort/request
configuration, and relative raw-evidence paths with SHA-256 digests. Its event
list can contain:

- `model_attempt`: one actual provider attempt, including schema preflight,
  grounding, repair, and failures. Usage is `reported`, `partial`, or
  `unavailable`; missing fields are null.
- `tool_call`: one standard-MCP operation, linked to the model attempt that
  caused it or explicitly null for an orchestration call.
- `task_score`: one independent final-state oracle result tied to a state hash.

The summary counts every recorded model attempt. It emits token totals only
when both token counts are reported for every attempt; otherwise both totals
remain null and `usage_status` is `incomplete`. With no model attempts, zero is
reported only when the event record explicitly contains none. A `task_success`
field on a runtime tool result is never treated as independent task success.
The validator checks raw-reference path and digest syntax, but does not open or
hash the referenced files and cannot prove the event stream is exhaustive.
When a provider adapter supplies the optional `cached_input_tokens`,
`cache_write_input_tokens`, `reasoning_output_tokens`, and `image_input_tokens`
fields, the summary carries a separate total for each. Each detailed total is
null unless that field is known for every attempt; `detailed_usage_status` is
`complete` only when every detailed field is present on every attempt. These
provider-specific categories are preserved separately from input/output totals
because their billing/subset semantics can differ. Missing details never
become zero.

## Durable provider-to-MCP attempt recorder

[`provider_attempt_recorder.py`](provider_attempt_recorder.py) adds a generic,
local recording boundary for an injected provider callable and an injected
standard-MCP transport callable. It does not choose or launch a provider. Use
one private, exclusively owned output directory per task.

`ProviderAttemptRecorder.invoke` writes the exact caller-supplied request bytes
and fsyncs a `model_attempt_started` row before calling the provider. It then
stores returned response bytes and usage/status, or writes a failed/timeout/
cancelled row with unavailable usage before re-raising the original exception.
`begin_tool_call` / `finish_tool_call`, `invoke_tool`, and
`invoke_tool_async` do the same around an MCP operation. When known, the
completed model generation is joined by `model_attempt_id`. Passing
`attempt_id=None` records an explicitly unlinked MCP operation when provider
context lives outside the relay; it does not infer a model attempt or token
usage. Tool raw filenames use a bounded digest-derived component, so maximum-
length accepted IDs remain portable on Windows.
All raw files have SHA-256-bound references in the journal; reconciliation re-reads the
bytes, checks their digests, and exposes missing, mismatched, or unparseable MCP
response data. The shared ledger rejects an MCP response/result mismatch.
`invoke_async` and `invoke_tool_async` support awaited provider and MCP
callbacks. They persist the start receipt before the first await, record
`asyncio.CancelledError` as a cancelled terminal attempt, and then re-raise it.
`record_task_score` can append one terminal score certificate after every
provider/MCP operation has finished, retaining the scorer's canonical state
bytes and digest with its scorer ID and `true` / `false` / `unknown` verdict.
The recorder validates and preserves this caller-supplied certificate; it
cannot establish that the scorer was truly independent. Recording a score also
prevents later attempts from being appended to that run.
The recorder resolves the raw directory at startup and before each write; it
refuses a path that no longer resolves to the run's direct `raw/` child. The
caller must still provide a private, exclusively owned run directory.

The local `test_mcp_endpoint_composition.py` tests drive asynchronous fake
provider results into the actual public `interface_guarded_compiled` FastMCP
entry point with the existing deterministic Fake X owner. The additive
[`recorded_public_mcp_caller_v1.py`](recorded_public_mcp_caller_v1.py) adapter
now supplies the reusable provider-attempt and public-Relay call boundaries
used by the image/stale-generation composition cell; it persists each tool
request before `Relay.request` and retains the complete returned envelope. Its
`invoke_generation_to_tool` path submits only completed generations with
captured response bytes; a failed generation is durably recorded without a
tool submission.
This is a research composition adapter, not an automatic hook in the frozen
integrated-efficiency runner or every production provider/orchestrator. The
success cell joins the generation-bound profile request to the tool receipt,
matches the returned MCP text payload to its result object, and counts
reported usage. The
Fake X child writes its initial and final 32x32 BGRX state to a test-only side
channel. A separate pixel oracle verifies that pixel (1,1) changed from
non-red to red, then records the final state bytes and score in the task
ledger. A second cell changes the process generation after the fake provider
returns its stale request; the standard caller admits zero transitions, the
state remains unchanged, replay is denied, and the same oracle records a false
task score. Both public MCP results keep `task_success=null`. These are
synthetic Fake X results only; the fixture has no real provider, production
application, external scorer, native input, or live task. The saved response is
the returned MCP text block, not a network-wire capture.

The added `test_fake_provider_image_and_stale_generation_roundtrip_public_relay`
also sends the observation and compiled action through `Relay.request` before
the actual FastMCP server. It preserves the returned `ImageContent` base64
payload byte-for-byte in the fake provider request, records the complete relay
request/response envelopes, then changes process generation while the fake
provider is complete but before the compiled tool call. The public caller
returns `SAFE_YIELD` with zero transitions; the independent Fake X pixel
oracle records false, and ledger reconciliation matches all three relay
responses while retaining usage and request bytes. This is an in-process Relay
composition test, not a stdio subprocess, real provider, external usage-log
reconciliation, live application, or task qualification.

One run of both composition cells, including the exact recorder journals,
request/response bytes, Fake X owner receipts, and scorer-state bytes, is
preserved in [`composition-evidence-20261020`](composition-evidence-20261020/README.md)
with a per-file SHA-256 manifest. It records the tested synthetic outcomes; it
does not increase their scope.

`test_independent_task_score_is_terminal_and_preserves_state_bytes` verifies
the journal contract for a caller-supplied score certificate. The composed
tests additionally run a small pixel oracle against the Fake X side channel;
the recorder preserves the certificate but cannot establish independence of a
production scorer or exhaustiveness of an external provider log.

An unfinished call makes strict reconciliation fail. A newly created recorder
session cannot silently resume it or start later attempts in the same run
directory. This makes interruption visible instead of turning an absent terminal
record into zero calls or a successful result. Partial/unavailable usage stays
unknown, and a runtime result's `task_success` is still not an independent task
score.

This is `PASS_CONTRACT_SCOPED` for the local recorder/composition contract,
one synthetic Fake X before/after effect predicate, and one stale-generation
refusal through both the direct public-MCP test seam and the in-process
JSON-lines Relay request path. It remains a Fake X contract result.
The wrapper cannot prove that an external orchestrator routed every model call
or MCP operation through it. The caller must pass exact captured wire bytes;
when bytes are unavailable, the receipt says so. No actual provider, GUI, WSLc,
Docker, allocation, application effect, release, or efficiency experiment ran.
Next: adapt the current provider/orchestrator and standard caller to this
boundary, then reconcile the emitted attempts and MCP calls against independent
provider logs before claiming completeness.

## H / T / D / C / U

- **H:** This envelope can prevent a future comparison report from silently
  dropping failed model attempts, treating missing provider usage as zero, or
  substituting a runtime verdict for an independent task score.
- **T:** Validate a pinned one-task record with complete, incomplete, and
  absent usage; model-to-tool joins; frozen conditions; raw references; and an
  independent score. Reject duplicate, dangling, malformed, or escaping
  references. Run the validator in normal and optimized Python.
- **D:** `PASS_CONTRACT_SCOPED` only for these local validation rules. It does
  not establish the ledger's exhaustiveness against provider logs or runtime
  transport, actual token usage, any product/live task effect, release,
  recovery, latency, or efficiency. The one synthetic pixel transition is
  scoped to its Fake X fixture.
- **C:** The caller currently operates at an MCP boundary while model usage is
  owned by the outer provider/orchestrator. The validator cannot observe that
  external boundary unless a future adapter emits and reconciles those raw
  receipts.
- **U:** No production provider adapter, model call, current GUI task, resource
  allocation, physical release, or independent production-application run is
  included. Missing usage stays unknown; referenced file existence/digest
  matching is not verified, and this packet is not a live result.

## Local check

```powershell
python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_ledger.py
python -O -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_ledger.py
python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_provider_attempt_recorder.py
python -O -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_provider_attempt_recorder.py
python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_mcp_endpoint_composition.py
python -O -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_mcp_endpoint_composition.py
```

The next integration step is to adapt actual provider request/response receipts
and the existing public MCP caller to this recorder, then independently
reconcile its ledger against provider logs. A live comparison still requires a
separately verified eligible allocation; #7924 remains STOP/HOLD.
