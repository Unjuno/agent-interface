# Issue #5851 successor — route-label consistency check

**Result: FAIL_NO_COUNTEREXAMPLE** for the preregistered half-cost mismatch hypothesis.

The independent path enumeration found that the original candidate conservatively withholds the half-model numeric delta (null) and labels the case nonstationary. The displayed path remains critical under both tested numeric interventions; see `CANDIDATE_RESULT.json`.

## H / T / D / C / U

**H.** The original synthetic fixture's half-model intervention changes the selected route while the candidate reports numeric fixed-topology elasticity.

**T.** Read frozen #5851 fixture/candidate/result and independently enumerate explicit route costs under the exact half-cost model change and separate +80 ms rule. Preserve originals.

**D.** Counterexample only if the candidate emits a numeric half-cost model delta while the selected route changes. Observed false; classify FAIL_NO_COUNTEREXAMPLE. The independent enumeration has zero ambiguity under the stated costs. Record route-label inconsistency separately, do not inflate it into the preregistered hypothesis.

**C.** The declared alternate endpoint might not be intended as a competing route; the fixture's branch semantics may be incomplete.

**U.** Synthetic consistency only. No runtime, GPU, GUI, task, safety, performance, or causal optimization claim.

Allocation `CAUSAL-ELASTICITY-5851-BRANCH-INTERVENTION-20261001-01`; frozen main `b1f916e2c32a75069c68d570b27c390c25de3c91`. Original candidate/auditor were not rerun. Full append-only provenance is in predecessor branch `research/causal-elasticity-5851-branch-intervention-successor-20261001`; this v2 file set is a corrected, current-main-aligned review copy, not a new experiment.
