# Issue #3858 — formal model-facing epoch-composition result

## Disposition

`PASS_MODEL_FACING_EPOCH_COMPOSITION_SCOPED`. The single frozen allocation completed all 12 scenario/policy rows using exactly 9 Qwen responses; the independent OrbStack audit passed all 23 integrity, input, policy and decision checks. No retry, action or effect occurred.

## H / T / D / C / U

- **H:** Under valid image transport and JSON mode, the typed epoch-aware policy answers coherent and bounded-skew cases correctly, rejects the cross-epoch conflict before inference, and exceeds zero-skew-only rejector exact coverage.
- **T:** Three frozen cases × four policies, with the same model/prompt/options and no task actions. The only changes from the v2 STOP chain were the standards-valid PNG filter byte and literal Ollama `format: "json"`; the independent bridge/auditor also now preserves and checks transport bytes.
- **D:** PASS requires 12 rows, 9 exact model responses, all three typed answers exact, conflict rejected before inference, typed exact count greater than `EPOCH_REJECT_ONLY`, bound model/source/provenance and valid PNGs, raw request/response links, and corruption controls. All passed.
- **C:** Local `qwen2.5vl:7b` digest `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`; Ollama 0.34.2; pinned linux/arm64 OrbStack/Obstac container; network none, read-only source, host loopback bridge only.
- **U:** This completes only the three-case model-facing first rung. It does not complete #3204's broader held-out channel matrix or prove general multimodal reasoning, recovery-time benefit, GUI correctness, production reliability or efficiency.

## Matrix outcomes

| Policy | Exact / 3 | Model calls | Answers (aligned, bounded skew, conflict) |
|---|---:|---:|---|
| `TYPED_EPOCH_AWARE_COMPOSER` | 3 | 2 | READY, READY, ABSTAIN (conflict rejected before model) |
| `EPOCH_REJECT_ONLY` | 2 | 1 | READY, ABSTAIN, ABSTAIN |
| `LATEST_CHANNEL_WINS` | 2 | 3 | READY, READY, BLOCKED |
| `BEST_EFFORT_MERGE` | 2 | 3 | READY, READY, BLOCKED |

The typed candidate retained bounded-skew coverage that the reject-only policy discards. On the deliberate cross-epoch conflict, latest-channel and best-effort controls returned `BLOCKED` rather than the oracle `ABSTAIN`; the candidate and rejector made no model call and abstained. Thus this fixed comparison's measured benefit is scoped to exact answers and safe conflict disposition, not generalized task quality.

All 9 model requests completed with JSON-mode transport and exact model identity. Per-call latency varied from 0.40 s to 9.87 s; the sample is too small and uncontrolled for any latency or efficiency claim. Total model-call counts by policy are retained in `formal/output/RESULT.json`.

## Evidence and integrity

- Formal invocation: 1; eligible model requests: 9; completed responses: 9; retries: 0; actions/effects: 0.
- Corrected generated PNGs pass CRC, decompressed row-length, filter-0, and center badge-pixel checks; the independent auditor also rejects CRC-valid PNG fixtures with filter byte 255.
- The auditor recomputes expected policy disposition and exact prompt independently, then validates internal request records, exact outgoing `/api/chat` payload bytes, exact HTTP response body bytes, model digest, and all request/response bridge receipts.
- `RESULT.json` SHA-256: `e84df9be0f79d79859afd5323f2995d55fbf84f6bdcdfbf30ab3d8085d3cf860`
- `BRIDGE_SUMMARY.json` SHA-256: `e5ad3e6a4e9dbf75b03dfa9f9a28a56b06588787ce28700727a3ada38cdc9bf1`
- `AUDIT.json` SHA-256: `3869e736765a3750eb4bc2015b339ac5374017cc79be9c786bccd1faa8b5557c`
- First request/response record SHA-256: `09753b0dd8c2769d9a046c9bc5effddf8bb41b706a634977dd984dc63d4d26b0` / `6151f49a4a61d6531cf4745cdf83229809bc67b3b99f49c4800b2ab01bf74c90`

All 9 request and response records, exact API payload/body base64, images, source freeze, execution record, construction output and isolated audit inputs/output are retained beside this report. The prior #3204 v2 and #3827 STOPs remain immutable; #3843 remains a separate one-cell compatibility result.
