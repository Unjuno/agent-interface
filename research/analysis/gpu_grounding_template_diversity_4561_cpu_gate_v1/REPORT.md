# CPU renderer and coordinate-oracle gate result

**Disposition: `PASS_CPU_RENDERER_COORDINATE_GATE`.** This is a construction
result only. The formal CUDA allocation on Issue #4561 remains
`STOP_CUDA_DETERMINISTIC_ADAPTIVE_POOL_BACKWARD` with zero training steps.

The frozen renderer emitted 12 source-template families and 48 PNG variants at
1280x800. All 48 decoded RGB hashes are unique. The 8 training and 4 held-out
families are disjoint; variants stay with their source family. A separate audit
re-rendered every image and matched pixels, PNG digests, geometry labels and
manifest. All 96 target coordinates are 32px-cell centers and the strict
compiled-form grounding contract accepted all 48 candidates. An out-of-bounds
coordinate corruption was rejected by the independent validator.

Manifest SHA-256: `249edc97bdd8882da6d5449fb074b46b75d2444dc592641674a73a5002ae433c`.
Formal optimizer steps: 0. CUDA calls: 0. GPU metrics: none. No model or
template-diversity hypothesis was evaluated. Results and scope are local-only;
the existing GitHub issue remains the canonical record of the frozen CUDA STOP.

Commands:

```text
python render_audit.py
python audit_cpu_gate.py out
```
