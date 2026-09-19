# Exact LP evidence-order revalidation

Issue #2576 is the source of truth for H/T/D/C/U and frozen gates.

This additive experiment reads the exact current `site/index.html` and both referenced media files from the checked-out commit. It generates a baseline and a candidate by swapping only the two existing media figures, then measures both in Chromium at 1440x900, 1024x768, 768x1024, 390x844, 360x740, and 320x568.

No result is claimed until `artifacts/RESULT.json` is independently inspected. The workflow must stop on missing assets or figure-boundary ambiguity. The candidate does not alter `site/index.html`.

Formal disposition vocabulary:
- PASS_EXACT_EVIDENCE_ORDER_SCOPED
- HOLD_ASSET_OR_SOURCE_MISMATCH
- HOLD_LAYOUT_ONLY
- FAIL_ACCESSIBILITY_OR_DISCLOSURE
