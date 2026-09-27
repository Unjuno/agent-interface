# Formal result — role-conditioned online LoRA rehearsal v1

**Disposition: HOLD_AUDIT_INTEGRITY.** The frozen one-shot run completed, but its registered independent auditor rejected two audit invariants. Do not interpret this as an audited scientific FAIL or PASS. The source, allocation, raw bytes, failed audit, and this supplemental diagnosis are preserved separately; formal seeds must not be rerun.

## Frozen run

- Issue: #4895; allocation `needle-online-lora-role-rehearsal-20260927-v1`.
- Base `main`: `c1e6f24d259f96b4d4dbf211e83fcdf6b9e0a4dd`.
- Image: `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64; offline, read-only source, one CPU, 2 GiB.
- Seeds: 735211, 735311, 735411; 3 arms × 16 arrivals × 3 seeds = 144 checkpoints.
- Container exit 0; one formal orchestration, zero retries; UTC elapsed 3.762 s.
- Raw JSON: 964,795 bytes; SHA-256 `ed4560d01c99adb74230758c6c6bb22458159d1b76e790836c0936c3cac15349`.
- Lossless compressed copy: `formal_result.json.gz` (SHA-256 `8754ceac5be2c46bb876ca0703a824337e395409caa8a69fe2eea72a1b00ab8`). Gunzip it to recover the raw JSON; decoded bytes must match the raw size and SHA above.

## Auditor disposition and diagnosis

The one registered auditor invocation exited 2 and reported `HOLD_AUDIT_INTEGRITY`, with `freeze_hash` and `duplicate_control_not_equivalent` for all seeds. It did not report any producer-replay/checkpoint errors.

1. The freeze sidecar was generated in standard `sha256sum` format (`<digest>  FREEZE.json`), while the auditor expects a bare digest. Independently computing SHA-256 of `FREEZE.json` matches the digest in the sidecar exactly; the auditor compared incompatible text formats.
2. The duplicated-B arm and single-B arm use mathematically equivalent mean cross-entropy gradients, but their independently batched floating-point kernels create small tensor/AdamW-state differences. The auditor incorrectly requires whole arrival JSON equality, including exact tensors and optimizer state, instead of validating each trajectory independently and treating duplication equivalence as a construction-level mathematical property.

These are auditor/specification defects. The original source and verdict remain unchanged. A new successor with fresh seeds must fix and test these conditions before its formal run.

## Raw descriptive observations only

Final heldout A/B accuracy:

| Seed | B_ONLY | B_DUPLICATE_CONTROL | A_REHEARSAL |
|---|---:|---:|---:|
| 735211 | 0.000 / 1.000 | 0.000 / 1.000 | 0.199 / 0.793 |
| 735311 | 0.000 / 1.000 | 0.000 / 1.000 | 0.590 / 0.488 |
| 735411 | 0.000 / 1.000 | 0.000 / 1.000 | 0.973 / 0.027 |

Rehearsal was unstable: none of the three seeds simultaneously retained A and acquired B at the preregistered 0.90 thresholds. The raw observations miss the quality criteria, but remain descriptive because the registered audit is HOLD. Per-update maxima were below 2 ms, well below the 60 ms bound; this tiny CPU task does not demonstrate end-to-end realtime usability.

## Excluded construction

Construction seed 735014 is separate from formal. One wrapper invocation stopped before fitting because it placed its own logs inside the required-empty raw directory (0 optimizer steps); a corrected wrapper ran construction once and its independent audit passed after adding an explicit base-immutability assertion. Construction final A/B: B_ONLY 0/1; duplicate control 0/1; rehearsal 0.773/0.027. This points in the same direction—preserving old-task performance can prevent B acquisition—but is not a formal row and is not pooled with the formal seeds.

The runtime/product is untouched. No claim is made about natural feedback, real-time systems, routing quality, production promotion, or action safety.
