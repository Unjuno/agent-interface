# H/T/D/C/U — #59 / PR #8094 current-main delta audit

## H
PR #8094 appears globally stale because its branch is 92 commits behind the intake main, but its execution-facing change may still be transplantable if current main has not changed the exact files it modifies. The hypothesis is that the large divergence is dominated by history/evidence paths rather than conflicts in the 10 runtime Python files plus one model prompt relevant to the proposed V15/per-key integration.

## T
Freeze merge base `21fecd58b9de30073c97234124e73b78c67d4b0c`, intake main `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028`, and #8094 head `d0aa8463a10abf04d1b40cb4f498fc0a659fb827`. Using GitHub object readback only, compare the 10 execution-facing Python paths selected from the PR patch plus `research/doom/map01_motor_responder_v10.txt`. A candidate addition is clean only if absent at both merge base and intake main. A candidate modification is nonconflicting only if the intake-main blob is byte-identical to the merge-base blob.

No production branch is changed, no live allocation is consumed, and no old result is rerun.

## D
`PASS_CURRENT_MAIN_DELTA_NONCONFLICT_SCOPED` iff all 11 paths are either clean candidate additions or candidate-only edits over a main blob identical to merge base, with zero path collisions. Any intake-main edit to a candidate-modified path is HOLD for explicit reconciliation. Missing object identity is STOP/HOLD.

## C
This is a source/transplantability gate only. Dependencies outside the selected paths, import order, behavior, stale tests, evidence-package validity, or the native audit FAIL retained on #8094 can still block integration. A conflict-free source delta is not semantic correctness.

## U
No V15/V39 process execution, X11, ViZDoom, model call, task effect, physical HID timing, independently useful feedback, bounded recovery, latency/token benefit, or merge approval. Same-author connector analysis is not independent human review.
