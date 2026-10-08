# Conditional parallax T0 — Issue #6079

Allocation: `CONDITIONAL-PARALLAX-6079-T0-20261003-01`\
Frozen main: `664f61e24b52fa2f955c486a6c714ca59629f6d9`\
Path: `research/analysis/conditional_parallax_6079_t0_v1_20261003/`

## H / T / D / C / U

**H — hypothesis.** In this declared pinhole-raster fixture, a verified nonzero lateral camera translation makes a rigid approaching target distinguishable from a screen-space scaling overlay using only timestamped pixels and the probe receipt. A sham (zero actual translation) and a noncontact world-anchored sprite whose visible trajectory is identical to the contacting target remain observationally equivalent and must yield `UNKNOWN`. No output establishes contact or grants authority.

**T — one frozen host-only experiment.** Generate nine fresh paired raster streams, each with five passive and three post-probe samples: three rigid-approach/screen-overlay pairs with actual translation, three matched sham pairs with zero actual translation, and three rigid-approach/noncontact-world-sprite pairs with the same visible 3-D trajectory. Vary three fixed approach schedules. Candidate input contains only opaque IDs, source bindings, timestamps, PGM bytes, and requested/actual probe receipt; truth labels are in a separate auditor-only file. Execute the candidate once on all nine pairs, then one independent raw-only auditor once. Run standard-library construction tests before formal freeze; no candidate run on the frozen corpus before freeze. Four corruption controls are evaluated on copies by the auditor without rerunning the candidate.

**D — disposition.** `PASS_CONDITIONAL_IDENTIFIABILITY_SCOPED` only if all nine pairs have byte-identical passive samples; all three actual-translation overlay pairs are distinguishable by target-to-background relative motion; all sham and identical-world-trajectory pairs are byte-identical throughout and return `UNKNOWN`; candidate never asserts contact/safety or authority; and the independent auditor has zero errors while rejecting all four frozen corruption controls. Any visible distinction in an equivalence pair, missed positive, malformed identity/clock/receipt, truth leakage, or control acceptance is `FAIL_METHOD`. Source/input drift or incomplete raw data is `STOP_INTEGRITY`. No retry or post-result threshold change.

**C — competing explanation.** The known probe may add information only because the renderer is a calibrated pinhole model and the target is a single rigid colored disk against a rigid landmark field. A practical application-specific screen may already expose simpler exact cues, or its renderer may erase this parallax distinction.

**U — limits.** Nine synthetic monochrome cases do not measure optical flow under noise, real camera motion, sprite semantics, harmful contact, GUI/game behavior, local YIELD benefit, release timing, task effect, safety, or MAP01 control. Identical observations with different hidden contact truth are not separable by any deterministic observer restricted to those observations. The raster generator and candidate share the declared feature encoding but the auditor is separately implemented and does not import either.

## Frozen method

- Raster: 128×96, PGM P5, grayscale background `0`, landmarks `100`, target disk `240`; focal length 72 px; camera center (64,48).
- Times: 0, 125, 250, 375, 500 ms passive; a requested +0.85 world-unit lateral translation is recorded at 500 ms; post-probe samples at 625, 750, 875 ms.
- Families and fixed schedules: three approach schedules, three sham schedules, and the same three schedules for identical-trajectory world sprites. Hidden semantic truth is auditor-only.
- Candidate statistic: per-frame target centroid minus all-landmark centroid; compare the paired streams after the probe. `DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS` requires an actual nonzero translation receipt and at least 2.0 px maximum relative-centroid separation. Otherwise return `UNKNOWN`. This is a pairwise observation distinction, not a contact classifier.
- No model, network, GUI, game, OS input, GPU, container, service, or shared resource. Host-only is permitted by #6079 T0 when no uncontested container is available; #5085's shared WSLc state remains untouched.

## Execution order

1. Freeze candidate, fixture generator, independent auditor, construction tests, visible input and truth sidecar hashes.
2. Re-fetch main and #6079; compare intervening paths and verify no branch/PR/worktree overlap.
3. Invoke frozen candidate once. Preserve raw stdout/stderr and output.
4. Invoke independent auditor once against exact frozen inputs/output; controls mutate copies only.
5. Run local relevant CI, source/hash/integrity checks, analysis index and workspace navigation checks.
6. Batch the completed evidence for review and merge only after local CI and PR gates.
