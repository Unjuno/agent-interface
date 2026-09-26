# Issue #3843 — formal outcome

## Disposition

`PASS_QWEN_VISION_BACKEND_PROBE_SCOPED` — the single preregistered call returned HTTP 200 and the exact expected JSON answer. The independent audit passed all 20 checks. This resolves only the narrow corrected-input probe; it does not establish multimodal recovery, composition, GUI effect, or general vision reliability.

## H / T / D / C / U

- **H:** A standards-valid filter-0 PNG lets the frozen Qwen2.5VL 7B request reach and return the expected READY answer, consistent with the predecessor's malformed PNG being the cause of its image-load STOP.
- **T:** One synthetic 448×280 RGB green badge, task-A/epoch-4 coherent text, the frozen prompt and JSON request, one call, no retry or fallback.
- **D:** PASS requires HTTP 200, exact model identity, byte-linked request/response, PNG validation and exact `{"answer":"READY"}`. Any provenance/transport failure is STOP; any completed nonmatching answer is FAIL.
- **C:** One local Ollama Qwen digest under the frozen OrbStack/Obstac contract. No GUI, task action, effect or recovery was exercised.
- **U:** This single corrected fixture is not a general vision or product capability claim and does not independently prove the predecessor STOP's cause beyond this controlled successor observation.

## Formal result

- Invocation budget: 1; submitted calls: 1; completed responses: 1; retry/fallback: 0.
- HTTP 200; response: `{"answer":"READY"}`; action calls: 0; effect claims: 0.
- Model: `qwen2.5vl:7b`, digest `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`.
- Corrected PNG SHA-256: `3f5342a50e97ac893472de6d78daa3b51a20cb54dced03dd088e015f7b0318d6`.
- Request SHA-256: `15fd036d0b0971a66f6b870ade3aa310e8106514a105fc11446ff50fb6b9b114`.
- Response record SHA-256: `f138ddbfe11b4d8efa7aa661fc2d6b6a53ce21904b527e9db357ffe8d6576ac4`; exact HTTP body SHA-256: `24cef847fc98d7f5b1267437af2867a5b3e7c79412c463f6ccae46a24d52bb7d`.
- Independent audit SHA-256: `cb4cda1fff04223c59f49b45a8a266de78da1350fdc72188fd016b862c6a5c46`; all 20 checks true, including PNG chunk CRCs, decompressed row lengths, filter-byte domain 0–4, source/prereg/freeze binding, exact model identity, one-call limit and response byte links.
- Runtime: 7.404 seconds measured by the bridge. OrbStack context; pinned linux/arm64 image; network-disabled container, read-only source; checked `OBSTAC_SOURCE_COMMIT`, `OBSTAC_IMAGE_ID`, `OBSTAC_FREEZE_SHA256`.

Raw request/response, response headers/body, runner result, execution record, image, freeze, and isolated audit inputs/output are retained beside this report. The predecessor #3827 STOP remains unchanged.
