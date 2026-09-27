# Issue #4853 — role-C support16/64 synthetic diagnostic (seed 7866401)

This one-shot successor to the immutable pre-fit STOP in #4848 tests the narrow support-count question against the exact #4749 main runner. It does not alter #4749's ten-seed result.

## Result

Pinned CPU Docker construction passed with zero updates; exactly one paired formal orchestration then completed. Independent raw-only audit reconstructed all six role cells, regenerated labels/predictions, checked the exact prefix and A/B pairing, and returned `PASS_RAW_AUDIT` with zero errors.

| Role | support16 | support64 |
|---|---:|---:|
| A | 0.9658203125 | 0.9658203125 |
| B | 0.9462890625 | 0.9462890625 |
| C | 0.908447265625 | 0.959716796875 |

C delta (64−16): **+0.05126953125** (+5.13 percentage points). Base immutable; 400 base updates and 120 B/C updates per C arm. PyTorch 2.5.1+cpu, one thread.

## Reproduction and provenance

`source/` contains the paired runner, shared prefix contract, construction test, independent auditor, and an exact copy of #4749's public main runner (Git blob `ecd3a0414178f38535406573314793a40b353878`). Read-back exact Git blob IDs for all five executable files are in [`SOURCE_BLOBS.md`](SOURCE_BLOBS.md). `FREEZE.json` preserves the preregistration snapshot; its `formal_invocations: 0` is the before-run state and is intentionally not rewritten. Formal command template, outcome and raw output digests are in `formal/`.

Image `needle-pilot05:local`, ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64 CPU; offline, read-only root/source, one CPU, 2 GiB RAM, 64 PIDs, dedicated output volume. No retry or seed substitution.

## Scope

One synthetic seed is descriptive only; no distribution/significance estimate, real-time online learning, GUI/task transfer, concurrency robustness, natural-skill transfer, product readiness, or action authority is established. Preserve #4848's STOP and #4749's independent formal result.
