# GPU pilot-04 STOP — capture channel lost

Issue: #5427  
Frozen allocation: six fresh-seed calls, 96 rows, no retries.  
Outcome: **STOP — allocation consumption and call count unknown; no auditable response recovered.**

The v4 memory-only runner was launched once on the Windows RTX 3080 host. During orchestration, the PTY event stream could not be decoded by the controller. The runner's final event was recovered after interrupting the live PTY. It reports `pilot_exit: EXCEPTION`, an empty captured `pilot_stdout.txt`, and no `calls.json` or `raw.jsonl` in its final in-memory file bundle. The final event's audit output is empty and `audit_exit` is null. No call event was durably persisted to GitHub before the controller lost its event channel.

The recovered inventory reports Ollama HTTP 200 and the expected installed model digests, but inventory is not evidence that any inference completed. A Qwen2.5 model was observed loaded at 100% GPU while the process was present; this does not establish a completed request, exact call count, response, or result. After interrupt, the runner exited. No inference retry or replay was made.

Therefore the allocation may have consumed a request, but the number of started/completed calls cannot be established. There are zero recoverable call records and zero auditable raw rows. No behavioral result or audit pass is claimed. Do not pool this attempt with earlier pilots. Preserve this STOP as-is; any further work must use a new successor issue, new seeds, and a runner/controller transport proven to preserve large call events durably before continuing.
