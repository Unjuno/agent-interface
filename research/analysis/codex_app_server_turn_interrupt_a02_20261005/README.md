# Codex App Server turn/interrupt construction A02

## Classification

This is one exploratory construction run, not a preregistered formal allocation. The command receipt and pass criteria were documented after the run. The candidate ran once with no retry.

## H / T / D / C / U

- **H:** On Codex CLI 0.160.0 for Windows, turn/interrupt using the active {threadId, turnId} cancels the App Server's pending Responses request to a localhost mock and completes the turn as interrupted.
- **T:** Start the installed App Server with a temporary CODEX_HOME, read-only thread sandbox, API credential variables removed, and a loopback-only mock Responses endpoint. Hold the first response behind a gate. Send one turn/interrupt with the actual returned thread and turn IDs.
- **D (written after the run):** Accept only if the RPC succeeds, exactly one held mock request disconnects before response release, the matching turn completes with interrupted, and the server reports no errors.
- **C:** This exercises the actual installed Windows App Server but substitutes an HTTP mock for the model provider. It measures App Server cancellation behavior in this setup.
- **U:** It does not show that any remote provider stops inference or billing, nor that physical input is released. It does not test model, GUI, game, useful feedback, recovery, ammo/progress, or terminal outcome. Windows timestamp resolution did not support latency reporting. The raw HTTP request body was not retained. Public output sanitizes local paths and session identifiers; the exact original local stdout hash is bound in provenance.json.

## Result

The candidate exited 0. The App Server accepted turn/interrupt with {}. Its pending HTTP client disconnected before the loopback server released a response, then the matching turn completed with status interrupted; one request was observed and the mock recorded no errors. A separate auditor validates the sanitized output and generated schema.

The generated 0.160.0 ClientRequest.json schema requires threadId and turnId for TurnInterruptParams; the extracted definition is published under schema/. At main b422026a83d0cdebbf5aa80df63fa883db4511ab, the production client blob 338b5fbdf436e14768274b9de6a3d3bb13fd274c sends that same payload; adapter blob 1a09c8752dff6a87bf8c180cb2e6fa7f43d4ad77 sets _cancellation_requested before the RPC and rejects later answers as stale.

## Evidence

- probe.py: one-shot candidate source.
- candidate.stdout: sanitized candidate result; original bytes remain locally preserved.
- candidate.command.json: sanitized command receipt, recorded after execution.
- audit_result.py and audit-independent.stdout: separate raw-output audit, plus an audit over this public sanitized result.
- schema/ClientRequest.json: generated schema from installed CLI 0.160.0.
- provenance.json: classification and raw-to-public hash link.
- SHA256SUMS: hashes for published files.


