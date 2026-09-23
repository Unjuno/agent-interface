# A2 result: safe HOLD under acquisition/scheduling tail

Scientific disposition per Issue #1476: **HOLD_LIVE_ANCHOR_NOT_SUFFICIENT_A2**. Promotion: **NO**. Formal logical allocation1; immutable batch invocations8; reruns/replacements/tuning0.

All 24 source-anchor arms expired with zero effects. Current-evidence anchoring admitted and produced the intended effect in 22/24 arms. The two misses were safe `EXPIRED` outcomes: pair1 capture-end to future application was 132.918531 ms (validity margin -12.918531 ms) and pair2 was 121.297729 ms (margin -1.297729 ms), both beyond the unchanged 120 ms evidence-anchored lifetime. Exact current digest/content still matched. Wrong effects, negative-control admissions/effects, authority grants and OS task input were all zero. Among admitted effects, future-to-effect p50/p95 were 1.161124/1.210474 ms.

The frozen `audit_a2.py` reports `FAIL_LIVE_ANCHOR_TRANSFER_A2` with `parent_evidence_anchor`. This is retained unchanged. It is a decision-rule implementation mismatch: Issue #1476 explicitly preregistered `HOLD_LIVE_ANCHOR_NOT_SUFFICIENT_A2` for safety-correct but incomplete positive recovery. No threshold/source/result is changed and no rerun is authorized. The 7 copied-result corruption mutations all remain rejected, but because the unmodified base result already fails the binary frozen auditor, those controls are not claimed discriminative for this failed base.

Postformal source integrity is exact: A2 source8/8 and parent #1227 source8/8 SHA-256 values match freeze. The complete raw first outcome (8 batch files, aggregate result, audit, controls and posthoc reconciliation) is retained losslessly in `RAW_ARCHIVE.json` + Base64 xz parts.

Interpretation: evidence anchoring fixes the source-timestamp provenance problem but a fixed 120 ms lease still loses eligibility when post-capture scheduling/fixture application tail exceeds the remaining 20 ms nominal margin. A later successor, if any, must isolate that post-capture tail or introduce a separately justified validity model; it must not lengthen the 120 ms duration post hoc or rerun this allocation.
