# Issue #6808 S06 — photometric encoding invariance

Allocation `LOOMING-VISUAL-ASSUMPTION-GATE-5905-S06-ORBSTACK-CONTRAST-20261003-01`.
This is a distinct synthetic method-sensitivity experiment, not a retry or
replacement for S01/S02/S03 and not a copy of their formal outcome. S03 remains
on its own WSLc branch/allocation; S04-ORBSTACK-CONTRAST stopped pre-invocation
because its base SHA did not match its branch HEAD. This fresh S06 lane uses a private OrbStack VM and
private Docker daemon as directly requested by the user in this task.

## H / T / D / C / U

**H.** The image-only component-geometry candidate's decision, reason, scale
and TTC estimate are exactly invariant when every binary background/foreground
pixel is remapped from `(0,255)` to either `(32,224)` or `(127,129)`, preserving
the frozen threshold mask at 128. The null is that near-threshold quantization
changes components or the detector's decision.

**T.** T0 only, no humans/model/input. Start with the 12 synthetic case families
from the #6808 S01 fixture design, and render three grayscale encodings each:
native, low contrast, and one-level-away-from-threshold. This yields 36 rows:
9 eligible positive rows (3 approaches × 3 encodings), 21 visible control rows
(7 controls × 3), and 6 rows forming three pairwise pixel-identical,
latent-cause-ambiguous controls. Candidate sees only opaque ID, image bytes,
timestamps and epoch; truth and encoding labels are withheld.

**D.** PASS_METHOD_SCOPED requires: each family has byte-for-byte equal output
fields other than opaque ID across its two transformed encodings; all 9/9
positive rows request the simulated cue at the frozen 0.30 s TTC threshold and
their TTC error is at most 0.06 s; no visible control requests a cue; each
pixel-identical latent-cause pair yields equal `UNKNOWN` outputs within all
three encodings; the independent raw-only auditor reconstructs 36/36 rows,
verifies threshold masks/hashes and rejects five preregistered corruptions.
Any false simulated release on a control, SAFE=true, output mismatch or audit
error is FAIL_METHOD. Source drift, image/path mismatch, incomplete run or
expired bounded window is STOP; retry budget is zero.

**C.** This probes only a deterministic scalar threshold and hand-rendered PGM
binary geometry. Its exact invariance is expected because the threshold masks
are deliberately preserved. It does not test sensor noise, antialiasing,
compression, color conversion, illumination gradients, real tracking or a
camera.

**U.** No game/GUI/runtime, natural images, model, human, input, task effect,
latency, safety, controller performance or user-benefit claim. An exact pass
supports only threshold-mask-preserving grayscale encoding invariance on these
36 finite synthetic rows.

Candidate and auditor each run once in separate digest-pinned containers with
`--pull=never --network=none`, read-only disjoint input mounts, distinct output
mounts, 1 CPU and 512 MiB. No retries or hidden labels in candidate input.
