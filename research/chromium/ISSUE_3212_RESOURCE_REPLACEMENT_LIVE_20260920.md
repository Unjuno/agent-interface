# Issue #3212 — live target/resource replacement invalidation (2026-09-20)

Additive resource-boundary evidence. Earlier records and full-issue HOLDs remain unchanged.

## H/T/D/C/U

- **H:** Replacing the target/resource invalidates the old receipt; only a receipt bound to the replacement resource may cause the live application effect.
- **T:** Three real Docker `--network none` allocations using `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, and CDP DOM observation. Each allocation changed the live resource marker from `resource-v1` to `resource-v2`, attempted the old receipt, then used a new resource-bound receipt.
- **D:** `PASS_RESOURCE_REPLACEMENT_AUDIT rows=3 errors=0`. Old receipt admission `0/3`; old DOM unchanged `3/3`; new receipt admission `3/3`; new DOM effect `3/3` (`title=saved:replacement`, `saved=true`, `value=replacement`). Raw SHA-256: `2dcaf121e5b3f0706ff202fb238b9aa9592eeef2ae075aed37a87c977bbd2c28`.
- **C:** `PASS_CHROMIUM_RESOURCE_REPLACEMENT_REACQUISITION_SCOPED`. The tested resource replacement path fails closed for the old receipt and succeeds only after rebinding.
- **U:** The resource marker is a controlled fixture boundary and does not cover every production target identity or cross-application resource lifecycle. Full reuse-benefit and generalization HOLDs remain.

Runner, fixture, raw trace, and independent auditor are under `research/chromium/issue-3212-resource-replacement-v1/`.
