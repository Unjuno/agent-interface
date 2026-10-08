# Issue #3843 — Obstac standards-valid PNG vision probe

Allocation: `issue3843-qwen-valid-png-orbstack-01`
Base main: `de9eb00fb05dc98d71607742eb0c90a4f2c041a1`
Path: `research/integration/issue_3843_qwen_valid_png_probe_v1/`

## H / T / D / C / U

- **H:** Qwen2.5VL 7B accepts the aligned request when the synthetic PNG uses the valid filter-0 scanline byte, and returns READY. This tests whether the predecessor's malformed image fixture explains its image-load STOP; it does not test composition or recovery.
- **T:** Exactly one synthetic aligned green badge, task-A, epoch 4, zero skew; standards-valid 448×280 RGB PNG SHA-256 `3f5342a50e97ac893472de6d78daa3b51a20cb54dced03dd088e015f7b0318d6`; same prompt and JSON-mode request contract as #3827. Oracle `{"answer":"READY"}`. One request maximum, no retry/fallback. Preserve exact request, HTTP status/headers/body, model identity and audit.
- **D:** PASS only on HTTP 200, verified model digest and exact schema-valid READY. A completed wrong/invalid answer is FAIL for this narrow probe. Any transport/image/model/provenance error is STOP. No retry.
- **C:** Separate additive issue/allocation/path. Use Obstac/OrbStack (`docker context orbstack`, pinned linux/arm64 image, network none, read-only source/root, dedicated writable evidence mounts), with checked `OBSTAC_SOURCE_COMMIT`, `OBSTAC_IMAGE_ID`, and `OBSTAC_FREEZE_SHA256`. The host bridge contacts loopback Ollama only and persists HTTP errors before returning them. Construction is mock-only and uses no model request.
- **U:** One corrected synthetic image/model response establishes no general visual capability, comparative utility, multimodal epoch recovery, GUI effect, reliability, or the #3204 promotion gate. The predecessor malformed-PNG STOP remains immutable.

## Frozen identities

- Image: `issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51`, linux/arm64.
- OrbStack Docker context; engine Docker 29.4.0.
- Ollama 0.34.2; model `qwen2.5vl:7b`, digest `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`.
- `format: "json"`; temperature 0; seed 3843; max 32 generated tokens. PNG scanline filter byte is 0 on all rows.
