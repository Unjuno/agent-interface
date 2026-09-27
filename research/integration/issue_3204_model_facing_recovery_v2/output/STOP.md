# Formal allocation STOP

Allocation: `issue3204-model-facing-recovery-orbstack-02`  
Frozen preregistration commit: `675bd02a76008b4bc293eca30c2e02a1051c6b96`  
Formal task/model completions: **0**  
Submitted Ollama API requests: **1** (call ID `01`; no retry)

The first frozen aligned/typed cell was submitted to the pinned local model identity. Ollama returned **HTTP 400 Bad Request**. The host bridge terminated with an uncaught `urllib.error.HTTPError`; because no response object was written, the runner remained waiting for its frozen RPC timeout. I interrupted that waiting runner after confirming the bridge had exited. No subsequent request was issued. The HTTP response body was not retained by the exception handler and is unavailable; no diagnostic/retry request was made. Therefore this allocation did not measure answer quality and must not be interpreted as model FAIL or PASS. Classification: `STOP_MULTIMODAL_RUNNER` / transport-contract incompatibility, prior to a completed task response.

Retained bytes:

- `exchange/request-01.json`, SHA-256 `0425eae6c6710cc39c2c23490601ac2fe38464e5b5f94f077ed78d1fe412e823`
- `output/bridge.log`, SHA-256 `468441326d1d365198a00dbc9bf97d7a746df49c418fb151d7d6625096be179d`
- `output/images/aligned.png`, SHA-256 `333a60fd9a07bdccc8703c0dd2ecb0726dbfc74351f011851c87ab42c9ca5719`

No `RESULT.json`, model response, or independent scientific audit exists for this formal allocation. The pre-inference source freeze and Issue #3204 preregistration remain unchanged. Construction-only mock artifacts remain separate and are not formal evidence. Any follow-up must use a new allocation and successor Issue/comment; do not repair this allocation post hoc or reuse its formal slot.
