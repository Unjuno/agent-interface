# T1 A01 terminal STOP — 2026-10-08

**Disposition: `STOP_MODEL_TAG_IDENTITY_GATE`; no scientific result.** The frozen candidate process was invoked once and exited 1 after three completed local model calls. The separate auditor was not invoked because the candidate did not complete; retries were zero. The pre-run freeze remains unchanged and correctly records 0/0 invocations at freeze time.

## First outcome

- Candidate invocation: 1; exit 1.
- Completed model requests: 3; all were the first three query calls in seed 4101 / episodic-only / prefix 1.
- Every response ended with `done_reason=length`, `eval_count=128`, zero answer-response characters, and 481–510 thinking characters. The output budget was consumed by model thinking, so none produced a scored JSON answer.
- Before the fourth model request, the per-request model identity check read `/api/tags` and found multiple entries named `gemma4:e4b`, so it stopped before issuing that request. Post-run read-only inventory showed duplicate `gemma4:e4b` entries with digests `537f7e16…` and `a3d2b953…`, while the frozen digest `c6eb396d…` was listed as `gemma4:latest`. This indicates a mutable/ambiguous tag name in the host registry; it is not evidence that the captured three completions used a different digest. Raw records retain the initial digest and exact response.
- Raw JSONL: 3 rows, SHA-256 `2e2634ea64abb45e78687902fcdf05be4f3d713166430904cebe8a89617ae34a`.
- Candidate stderr: SHA-256 `b85ff852f2245a5b433530f7137630e10ce086ed67441b74d99c45f2c269902b`.
- Candidate stdout is empty. No audit JSON exists.

The first formal outcome is preserved unchanged. Do not restart this allocation, run its auditor, or interpret partial rows as a model result. A future distinct allocation would need a fresh seed set, immutable/digest-verified model naming (`gemma4:latest` currently points to the frozen digest), and `think:false` in every Ollama request; these are prospective deltas, not amendments to A01.
