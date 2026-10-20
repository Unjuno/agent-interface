# Standard MCP task ledger v1 — offline contract check

Status: local measurement-infrastructure construction only. This does not run a
model, GUI, WSLc, Docker, or a formal allocation, and does not qualify the
integrated route.

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

## Durable provider-to-MCP attempt recorder

[`provider_attempt_recorder.py`](provider_attempt_recorder.py) adds a generic,
local recording boundary for an injected provider callable and an injected
standard-MCP transport callable. It does not choose or launch a provider. Use
one private, exclusively owned output directory per task.

`ProviderAttemptRecorder.invoke` writes the exact caller-supplied request bytes
and fsyncs a `model_attempt_started` row before calling the provider. It then
stores returned response bytes and usage/status, or writes a failed/timeout/
cancelled row with unavailable usage before re-raising the original exception.
`begin_tool_call` / `finish_tool_call` or `invoke_tool` do the same around an MCP
operation and join it to the completed model generation by `model_attempt_id`.
All raw files have SHA-256-bound references in the journal; reconciliation re-reads the
bytes, checks their digests, and exposes missing, mismatched, or unparseable MCP
response data. The shared ledger rejects an MCP response/result mismatch.
The recorder resolves the raw directory at startup and before each write; it
refuses a path that no longer resolves to the run's direct `raw/` child. The
caller must still provide a private, exclusively owned run directory.

An unfinished call makes strict reconciliation fail. A newly created recorder
session cannot silently resume it or start later attempts in the same run
directory. This makes interruption visible instead of turning an absent terminal
record into zero calls or a successful result. Partial/unavailable usage stays
unknown, and a runtime result's `task_success` is still not an independent task
score.

This is `PASS_CONTRACT_SCOPED` for the local recorder/composition contract only.
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
  transport, actual token usage, task effect, release, recovery, latency, or
  efficiency.
- **C:** The caller currently operates at an MCP boundary while model usage is
  owned by the outer provider/orchestrator. The validator cannot observe that
  external boundary unless a future adapter emits and reconciles those raw
  receipts.
- **U:** No provider adapter, model call, current GUI task, resource allocation,
  physical release, or independent application run is included. Missing usage
  stays unknown; referenced file existence/digest matching is not verified, and
  this packet is not a live result.

## Local check

```powershell
python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_ledger.py
python -O -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_ledger.py
python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_provider_attempt_recorder.py
python -O -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_provider_attempt_recorder.py
```

The next integration step is to adapt actual provider request/response receipts
and the existing public MCP caller to this recorder, then independently
reconcile its ledger against provider logs. A live comparison still requires a
separately verified eligible allocation; #7924 remains STOP/HOLD.
