# Post-hoc per-row audit of the retained #4150 comparator

Allocation: target-belief-audit-4150-posthoc-01
Issue: #4609
Predecessor: #4150 / ID003, preserved without modification.

## H

The frozen ID003 auditor checks only the aggregate number of unsafe top1 ALLOW rows. It can miss reassignment of those decisions among semantic strata. An independent implementation of the frozen comparator should verify each retained row and reject a copied result that moves six false ALLOWs from valid ambiguous rows to invalid-provenance rows.

## T

Read the unchanged formal result at research/integration/issue_4150_target_belief_admission_id003/FORMAL_RESULT.json (SHA-256 6a391d2496c82282c66446213fdfc46e437baa512e4100697bc431a307a5d490). Comparator source is the frozen research/analysis/target_belief_admission_v3/experiment.py (Git blob 3d0d730d834d939f291051cdc8c9060df3492131, SHA-256 3d117395dba99ec483b7df36b06dc9e9483c8b2881a83f38a1f6a7668c173314). Independently derive each expected decision: REJECT for non-VALID provenance, empty scores, or max(score) < 80; otherwise ALLOW.

For a copied result only, change r24/r25/r32/r33/r40/r41 from ALLOW to REJECT and r02-r07 from REJECT to ALLOW. Update companion false-allow and authority fields consistently. Compare both the frozen auditor and the independent per-row oracle on baseline and copied data. Do not alter or rerun formal rows.

Local preliminary probes before this freeze are excluded construction. The frozen audit-gap probe source and gates are published in FREEZE.json and read back before the one bounded Docker diagnostic execution.

## D

The expected post-hoc decision is an audit-integrity finding, not a new scientific outcome:
- baseline formal result hash unchanged and frozen auditor passes;
- independent per-row baseline mismatch count is 0;
- copied result retains aggregate top1 false-ALLOW count 6;
- frozen auditor accepts that copied result;
- independent per-row checker rejects it and identifies all 12 altered rows.

The actual retained rows remain consistent with the comparator. Preserve ID003's scientific PASS unchanged while reporting the aggregate-only mutation blind spot.

## C

One finite 64-row retained synthetic result and one deliberately corrupted copy. This is an audit stress probe, not a detector accuracy or natural error-rate estimate. No model, optimizer, GUI, input, or runtime authority is used. The top1 oracle is reimplemented directly from frozen constants and does not import the frozen auditor's expected-value function.

## U

This addresses one demonstrated mutation class only. It does not establish live visual-target quality, probe safety, task completion, product readiness, or completeness of all possible audit corruption controls.