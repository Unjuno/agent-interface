# Issue #3827 — Obstac one-cell local vision JSON-mode probe

Allocation: `issue3827-obstac-json-probe-orbstack-01`  
Base main: `07c231463ebb45074444a957166956711103fadc`  
Path: `research/integration/issue_3827_obstac_json_probe_v1/`

## H / T / D / C / U

- **H:** The pinned local Qwen2.5-VL vision model accepts one `/api/chat` request using Ollama JSON mode (`format: "json"`) and returns a schema-valid status for an unambiguous aligned green-badge fixture, despite the prior #3204 schema-object request stopping with HTTP 400.
- **T:** Exactly one synthetic aligned case: green badge image and coherent task-A records, epoch 4, zero capture skew. Oracle is `{"answer":"READY"}`. Exactly one request maximum, no retries. Prompt carries the one-key answer schema; API `format` is literal `json`. Retain exact HTTP status/headers/body on both success and error, request/response hashes, model identity, image/prompt hashes, tokens, timing, and bridge receipts. No action/effect calls.
- **D:** PASS only if HTTP 200, matching pinned model identity, and parsed answer is exactly `{"answer":"READY"}`. A complete valid model response with a wrong or malformed answer is FAIL. Source/provenance/model/HTTP/RPC errors are STOP. No fallback or second request.
- **C:** This is a new branch and allocation after the immutable #3204 allocation-02 STOP. Use Docker context `orbstack` under the repository's Obstac execution convention, `linux/arm64`, `--network none`, read-only root/source, resource limits, fresh dedicated writable result/RPC mounts, and frozen `OBSTAC_SOURCE_COMMIT`, `OBSTAC_IMAGE_ID`, `OBSTAC_FREEZE_SHA256` environment bindings checked by the in-container runner. Only a host-side loopback bridge can contact Ollama; it preserves the exact HTTPError response bytes. Construction uses a mock bridge and makes zero Ollama calls.
- **U:** PASS would establish only one local vision JSON-mode request for this model, version, synthetic image and prompt. It does not validate epoch composition, bounded-skew recovery, comparative utility, GUI interaction, production reliability, or the full #3204 decision gate. The predecessor's HTTP 400 and missing-body limitation remain unchanged.

## Frozen environment

- Image: `issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51`, linux/arm64.
- OrbStack Docker context; engine reported as Docker 29.4.0.
- Local Ollama 0.34.2; `qwen2.5vl:7b`, digest `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`.
- Temperature 0, seed 3827, maximum 32 generated tokens, one image.
