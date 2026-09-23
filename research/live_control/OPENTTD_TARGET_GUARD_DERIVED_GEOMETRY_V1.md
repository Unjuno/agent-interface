# OpenTTD path-derived target/guard geometry v1

The interface can now derive the local visual condition from an already admitted
two-segment pointer plan. Each point in the first drag gets a 12x8 target box.
The continuation's shared visual corner is checked within an 8px tolerance and
excluded; its remaining points get disjoint 12x8 guard boxes. Invalid point
shapes, duplicate points, distant corners and overlapping boxes are refused.
The pure probe also verifies translation equivariance on Windows and WSL.

Frozen seed991004 frames calibrate the derived boxes before fresh input. An
unchanged pair returns `target_not_reached` with zero target pixels, the settled
first segment returns `met` with 139 target and zero guard pixels, and the later
segment returns `guard_changed` with 157 target and 113 guard pixels. Source and
image hashes plus recomputed outcomes audit on Windows and WSL. This selection is
posthoc and uses a development-known path, so it is calibration rather than
held-out geometry evidence.

The first preregistered fresh pair is retained as a failed negative-control
design. Moving the first drag up 16px was expected to create a wrong row, but
OpenTTD snapped both drags to the same tiles. Both cases therefore met the local
condition and independently completed the intended five-tile L. The interface
and engine scorer agreed; the experimental assumption was wrong. The failure
retains 70 exactly replayed frames and all release, process, source and save
checks.

A separately preregistered completed-segment repeat provides a valid negative on
the same changed save. A-to-B is built before the source observation, then the
same drag is repeated. Both samples contain zero target change and one guard
pixel; the condition returns `target_not_reached`, B-to-C never starts, and the
independent task score remains false while forbidden and surrounding tiles stay
unchanged. The 36 exact frames and lifecycle checks audit on Windows and WSL.

Combined, the fresh seed991004 evidence supplies a positive target case from the
retained pair and a separate repeat negative. It is not a matched correct
positive/negative pair because the preregistered wrong-row input aliased to the
positive under tile snapping. First/repeat drag to local condition remains
2.46–2.55 seconds. The path came from a prior model run, while the current
episodes are scripted; there is no model, token, human-tempo or broad geometry
generalization result.

Decision: retain the derivation candidate and both the failed and successful
negative controls. Next use a preregistered held-out screen transform or a newly
authored path, derive boxes without manual edits, and require local classification
to agree with the independent engine score.
