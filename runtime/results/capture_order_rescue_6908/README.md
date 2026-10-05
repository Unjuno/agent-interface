# Composed rescue of #6908 capture-order repair

Exact original source: `2cb3873bf54882904b1818467a77eb55d167906b`, PR #6908.
All 68 original packet files are unchanged. Its primary first count-gate FAIL
remains FAIL; the additive v2 is retained-data reconciliation, not a new primary
PASS. The 66 rows and eight copied-output corruption witnesses are preserved.

Production composition adds only the eight capture-order lines and original
five-method regression file to current main. It keeps later exact-integer
admission-sequence and successful-effect-reference guards, plus their docs.
Capture ordering is checked in the declared shared monotonic domain, not clock
authentication, independent application-effect certification or physical release.

Fresh local test-first outcomes:

- Current-main five-method regression: ten expected failing subcases, exit 1.
  Retained local log SHA256 `f022bbdc5b814ba3d79bfe3e073e7a53ca229547eee6b4772e5eab298b5f1445`.
- Initial whole-file trial composition: 92 methods, 22 failing subcases, exit 1,
  because the old snapshot removed later admission/effect guards. This is an
  integration failure, not a passing source. Retained local log SHA256
  `a676dc07f84f50f688f7e33ffb5c9c5d75ff0817eff776cc9bc2499fe0b1c689`.
- Restoring both later guards and effect-reference documentation leaves an
  additive eight-line source diff. Complete current core: 92/92 PASS normally
  and 92/92 PASS under `-O`. No test removed or expectation relaxed.

`python -B runtime/results/capture_order_rescue_6908/test_archive.py -v`
validates all 67 manifest hashes/public projections and runs both full raw-only
auditors on a private temporary copy. Exact old stdout JSON must match; original
auditor exit 1 is required, supplemental exit 0 is required. Assert-based archive
auditors are intentionally not validated with `-O`. No old matrix/producer or
shipping allocation is rerun. Private logs/working-source mixed-newline identities
are not relabeled as public canonical bytes. All original limits remain.

A further current committed-tree distribution check builds a fresh portable
archive, compares its compiled module bytes with the composed production source,
and executes all five original regression methods in an isolated `-I` child
outside the checkout, importing only the archive runtime. This is new ordinary
distribution engineering, not a repeat of the original shipping allocation.
