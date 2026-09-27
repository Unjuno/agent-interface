# #3446 Skill / Adapter Router — finite authority-neutral rung

Allocation: `skill-router-adapter-selection-3446-20260923-01`
Base main: `ec42ffec1c093a14c270fb1758f8bf93f8f25a12`

## H
An evidence-bound deterministic router using declared capability scope, current evidence epoch, availability, a frozen confidence threshold, and interference state can select the one compatible browser/file/GUI adapter or YIELD correctly. A confidence-only comparator should expose wrong routing on directed stale, unavailable, scope, interference, and cross-domain ambiguity controls.

## T
No GUI/input/model/provider/network. Standard-library only.
Formal corpus: 48 rows, six each of NOMINAL_BROWSER, NOMINAL_FILE, NOMINAL_GUI, CROSS_DOMAIN_AMBIGUOUS, ADAPTER_UNAVAILABLE, STALE_CONTEXT, SCOPE_MISMATCH, INTERFERENCE. Policies: CONFIDENCE_ONLY and EVIDENCE_BOUND. Threshold=0.75. One adapter per nominal request; cross-domain requests require more than one adapter and therefore YIELD in this first-rung single-adapter router.

Every adapter proposal has adapter_id, scope, confidence, available, evidence_epoch, interference. EVIDENCE_BOUND filters exact scope, current evidence epoch, availability, no interference and confidence >= threshold; routes iff exactly one eligible candidate remains, otherwise YIELD. Router output never grants authority.

## D
PASS_SKILL_ROUTER_ADAPTER_SELECTION_SCOPED iff EVIDENCE_BOUND matches the independent oracle 48/48; wrong adapter routes=0; required-YIELD violations=0; unnecessary YIELD=0; authority grants=0; and CONFIDENCE_ONLY exposes at least 12 wrong/non-YIELD directed-control rows. Independent raw-only audit errors=[] and >=10 coherent corruptions reject.

FAIL_ROUTER_SCOPE_OR_FRESHNESS on any candidate wrong adapter. FAIL_ROUTER_UNCERTAINTY_BOUNDARY on any required YIELD violation. HOLD_NO_ROUTING_DISCRIMINATOR if comparator wrong/non-YIELD rows <12. Missing source/denominator/audit evidence => HOLD/STOP.

## C
Authored deterministic request classes/confidences are not a natural workload distribution. Confidence calibration, router compute, adapter startup/switching and task effect are not measured.

## U
No learned router, real adapter execution, GUI/task correctness, model/token/latency benefit, action authority, or production promotion.
