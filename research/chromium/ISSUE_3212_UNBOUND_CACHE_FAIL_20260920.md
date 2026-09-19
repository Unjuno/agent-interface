# Issue #3212 — live unbound-cache unsafe witness (2026-09-20)

This is an intentional failing control, not a success result. All prior safe-path artifacts remain unchanged.

## H/T/D/C/U

- **H:** An unbound cache that admits a receipt after source-lineage change weakens the receipt gate and can cause an unsafe application effect.
- **T:** Three real Docker `--network none` allocations using `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, and CDP DOM observation. The live source marker changed from `source-v1` to `source-v2`; the intentionally unsafe control admitted the old source-bound receipt without rebinding.
- **D:** Independent Docker audit output: `FAIL_REUSABLE_RECEIPT_WEAKENS_GATE rows=3 unsafe_witnesses=3`. Source mismatch `3/3`; unbound admission `3/3`; unsafe DOM effect `3/3` (`title=saved:unsafe`, `saved=true`, `value=unsafe`). Raw SHA-256: `835749b54666da03a7d16c3d6eb0968825c255c1f41c692b44ce11465f5c744c`.
- **C:** `FAIL_REUSABLE_RECEIPT_WEAKENS_GATE`. The unbound control is rejected as a research policy; this is evidence for retaining source/generation binding, not a candidate implementation.
- **U:** The control is intentionally adversarial and scoped to this fixture; it does not quantify production incidence or model quality. Safe-path HOLDs remain unchanged.

Runner, fixture, raw trace, and independent auditor are under `research/chromium/issue-3212-unbound-cache-fail-v1/`.
