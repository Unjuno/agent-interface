# turn/interrupt A03 QPC timing candidate — STOP

## H / T / D / C / U — frozen before candidate

- **H:** Codex CLI 0.160.0 on native Windows will abort a held localhost Responses request on turn/interrupt; QueryPerformanceCounter-backed perf_counter can measure interrupt send, RPC acknowledgement, HTTP disconnect, and turn completion.
- **T:** One App Server session, temporary CODEX_HOME, read-only thread sandbox, API credential variables removed, localhost-only mock. Hold the first response until 1.0 s after interrupt send. Record event sequence and perf_counter_ns times. Candidate limit one; retries zero.
- **D:** PASS requires accepted interrupt, one request, disconnect before gate release, matching interrupted completion, no server errors, and high-resolution timestamps. Missing candidate output or any required transport event is STOP; no retry.
- **C:** Actual installed App Server, but no real provider, inference, game, GUI, or input.
- **U:** One sample cannot establish a latency distribution or SLA. Provider-side inference/billing remains untested.

## Outcome

The candidate exited 1 after Windows TemporaryDirectory cleanup raised PermissionError [WinError 32] while unlinking a background plugins-clone Git FETCH_HEAD. The runner failed before serializing candidate JSON. The temporary App Server session log was recovered independently: it contains a turn_aborted record with reason interrupted and duration_ms 111. That supports only an interrupted turn. It does not recover the turn/interrupt acknowledgement, HTTP disconnect, response-gate ordering, or latency measurements. Classification: STOP_EVIDENCE_INCOMPLETE. The frozen candidate ran once; no retry occurred.

The session log and original stderr remain preserved locally. Public artifacts omit their session IDs and local paths; provenance.json records their raw SHA-256 hashes. The extracted schema records the required threadId and turnId fields. This is a harness failure record, not evidence that the timing hypothesis passed or failed.

## Evidence

FROZEN.json and SHA256SUMS bind the prospective candidate and environment. candidate.runtime.json and candidate.exit retain execution status. recovery_summary.json is the sanitized extraction from the raw session log. audit_result.py independently validates the STOP classification and verifies that the missing HTTP/timing evidence is not promoted.
