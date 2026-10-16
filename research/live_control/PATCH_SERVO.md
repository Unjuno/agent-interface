# Bounded patch correction integration — 2026-09-13

`patch_servo.py` connects the patch effect sensor to existing session_v15 yields
through a scripted callback. The planner supplies a source patch, target delta,
maximum correction count and per-correction distance. The candidate keeps no input
authority: session_v15 and owner_v9 still validate each reply against original lease,
owner revision, focus/surface and reply deadline. Initial motion ends before replies.

The policy compares target displacement with observed patch displacement. It emits
bounded movement or finishes for local goal, lost/ambiguous tracking or update limit.
The original template is not updated. `finish` releases input but the backend reports
`completed` even when the controller reports `lost`: consumers must inspect controller
outcome and independent task score. This incomplete outcome mapping is not promoted.

## Retained real-app attempts

| Cohort / condition | Saved displacement | Controller result | Program time |
|---|---|---|---|
| 01 original position | 24 px | local goal | 664 ms |
| 01 attempted shifted setup | 0 px | lost | 473 ms |
| 02 original, deselected source | 24 px | local goal | 902 ms |
| 02 shifted setup | no trial | 41-point setup rejected (maximum 32) | — |
| 03 original, deselected source | 24 px | local goal | 799 ms |
| 03 shifted, deselected source | 24 px | local goal | 733 ms |

Cohort 01's coarse setup move did not move the object; it is not a new-position
trial. Source/feedback inspection shows selector handles present then disappearing
in the drag. Patch error 0.03188 exceeded the unchanged 0.03 threshold; the policy
finished without a correction. This is a practical decoration sensitivity failure.

Cohort 02 added a saved-displacement setup gate and explicit Escape/settle before
the source image. Its shifted setup erroneously had 41 points and failed validation
before input. Source manifests were written only after both cases, so this partial
cohort has no manifest. Its script and partial observations remain archived; do not
claim the same provenance coverage as completed cohorts.

Cohort 03 uses 21 setup points and verifies actual setup displacement. The shifted
source starts at SVG x=78.81356 (34 screen px beyond x=50 at fixed 118% zoom).
Both servo trials then move 24 px within ±1 px tolerance, with one local correction
and one goal/finish observation. Independent saved XML preserves y, width, height
and absence of transform. The target is the same single rectangle; this does not
evaluate unrelated objects, distractors, different zooms or multi-domain collateral.

All decisions are scripted. The fixture-specific source selector uses red_bbox
only to initialize the planner's patch; the correction policy reads image patches
and never queries red_bbox or XML. Saved XML is used for setup qualification and
post-action scoring. No claim of assistant-selected patches or equivalent remote
model work is made. Times bracket the local servo program and exclude setup,
selection clearing, save and independent scoring; they cannot be compared directly
to the previous 13.39 s assistant reply delay as a speedup.

`audit_patch_servo.py` verifies 69 exact frame reconstructions, available source
manifests, saved final attributes and all recorded terminal releases. Normal process
exits and finally cleanup were observed, without separate per-child exit attestation.

## Next gates

The selected-source failure remains unresolved; deselection is an explicit setup
condition, not evidence that matching tolerates decoration changes. Next test real
distractors/lost targets, outcome mapping, and planner-facing schema/target submission.
The callback is still synchronous with output emission; stall behavior retains the
existing deadlines and is not a real-time scheduling guarantee. No baseline promotion,
formal benchmark adoption, freeze credit, general servo claim or token saving.
