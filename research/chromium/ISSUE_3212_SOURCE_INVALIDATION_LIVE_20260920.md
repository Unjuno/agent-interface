# Issue #3212 — live source-lineage invalidation and reacquisition (2026-09-20)

Additive safety/effect evidence. Earlier records, including HOLD and adversarial artifacts, remain unchanged.

## H/T/D/C/U

- **H:** If source lineage changes during the model-wait interval, the old receipt must be rejected without changing the application; a newly reacquired receipt bound to the new source may produce the effect.
- **T:** Three real Docker `--network none` allocations using `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, CDP DOM oracle, and the same v2 generation-aware runner. Each allocation changed the live fixture source marker from `source-v1` to `source-v2`, attempted the old receipt, then reacquired a new receipt and dispatched through the application.
- **D:** `PASS_SOURCE_INVALIDATION_AUDIT rows=3 errors=0`. Old receipt admission `0/3`; old DOM unchanged `3/3` (`title=ReceiptFixture`, empty saved/value); new receipt admission `3/3`; new DOM effect `3/3` (`title=saved:changed`, `saved=true`, `value=changed`). Raw SHA-256: `381bff3cdf3c0e84c9a5af3e355ad06436b61bb0a63436b987362d0cf98cf2cf`.
- **C:** `PASS_CHROMIUM_SOURCE_INVALIDATION_REACQUISITION_SCOPED`. This fixture demonstrates fail-closed invalidation followed by a new-source effect, with an independent auditor.
- **U:** The source marker is a controlled fixture boundary, not proof of every production source-lineage mechanism. Model quality, broad held-out cases, and full reuse-benefit measurement remain open; `HOLD_REUSE_BENEFIT_UNMEASURED` is unchanged.

The runner, fixture, raw trace, and independent auditor are under `research/chromium/issue-3212-source-invalidation-v1/`.
