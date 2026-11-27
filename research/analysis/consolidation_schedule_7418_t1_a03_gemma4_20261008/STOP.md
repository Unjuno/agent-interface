# T1 A03 terminal STOP — duplicate loaded runner identity (2026-10-08)

**Disposition: `STOP_DUPLICATE_LOADED_RUNNER_IDENTITY`; no scientific result.** Candidate invoked once and exited 1 after one model request. Auditor was not invoked; retries were zero. The freeze manifest remains unchanged with pre-run 0/0 counts.

The candidate preflight observed one loaded `gemma4:e4b` runner at the frozen digest `c6eb396d…`. The first query returned valid JSON, `done_reason=stop`, 27 completion tokens, no thinking. Immediately afterward, `/api/ps` returned multiple `gemma4:e4b` entries, so the candidate recorded `running_digest_after=UNAVAILABLE` and stopped before request 2. A separate read-only `/api/ps` immediately after the stop showed two entries for the same name with digests `a3d2b953…` and `c6eb396d…`. The response itself carries no serving digest, so the first answer cannot be attributed conclusively and is not scored.

- Candidate exit 1; model calls 1; auditor 0; retries 0.
- Raw JSONL: 1 row / 3,929 bytes, SHA-256 `955d4aaf9434b805f5e2eb44c0619837399dbb64fc5c2d612aa463c629ca2e39`.
- Candidate stdout empty, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Candidate stderr SHA-256 `1785f41ced27563835177d706d2920cb9ecc575a55a9807ca7ae8b62b9938c8a`.

Do not resume, audit, or pool this partial output. A future allocation needs a model service whose loaded-runner identity remains unique through generation, or a private pinned model store. Earlier T1 A01/A02 STOPs remain unchanged.
