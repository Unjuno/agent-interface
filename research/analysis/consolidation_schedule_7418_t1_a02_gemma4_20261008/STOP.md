# T1 A02 terminal STOP — model tag drift (2026-10-08)

**Disposition: `STOP_MODEL_TAG_DRIFT_AFTER_17_CALLS`; no scientific result.** Candidate invoked once and exited 1 after 17 successful model calls. Auditor was not invoked; retries were zero. The freeze manifest remains unchanged and records the pre-run 0/0 counts.

All 17 responses were `gemma4:latest`, `done_reason=stop`, with JSON response text and no thinking field; `eval_count` ranged from 19 to 92. The candidate rechecked `/api/tags` before each request and observed the frozen digest through call 17. Before request 18, the exact tag had become ambiguous and no request was sent. A post-stop read-only tag inventory showed two `gemma4:latest` entries with digests `537f7e16…` and `9ec987e7…`, neither the frozen `c6eb396d…`. `ollama ps` still showed the loaded runner ID prefix `c6eb396dbd59`; this is consistent with a registry/tag mutation while the loaded model remained, but the output response itself does not carry a digest, so exact serving digest for each response is not independently proven.

- Candidate exit 1; completed model calls 17; auditor 0; retries 0.
- Raw JSONL: 17 rows, 77,610 bytes, SHA-256 `f7cee8f2276c361390065813d929b5e36241061ed1173944fd34c982899a818b`.
- Candidate stdout: empty, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Candidate stderr SHA-256 `e6bc388fe6a81c15e16482a6966bdc86e9f6660bfd76ad7fc7ba2d499fb4b5e7`.

Do not resume or audit this partial allocation as a completed result. A further distinct allocation would need a locally copied/frozen model manifest or another verifiably stable model identity, then a fresh seed set and path. A01's separate STOP remains unchanged; neither partial raw is pooled.
