# Spatial-block qualification of target-position gains

- **Source:** Open [Issue #6590](https://github.com/Unjuno/agent-interface/issues/6590), successor to [#4752](https://github.com/Unjuno/agent-interface/issues/4752). The question is whether a position-random held-out estimate can overstate performance on spatially blocked positions for a fixed synthetic visual model.
- **Current issue-level evidence:** The corrected T1 synthetic comparison, merged in [PR #6682](https://github.com/Unjuno/agent-interface/pull/6682), returned `H_FAIL_SCOPED` for its preregistered ≥0.20 random-minus-block gap. This does not establish equivalence, absence of spatial structure, or real-GUI generalization. Issue #6590 remains open for any separately justified follow-up.

## Evidence sequence

- **T0 method control:** `METHOD_PASS` on 12,800 authored synthetic rows. The independent auditor reconstructed every row; a planted local-failure field yielded a random-split minus worst-block gap of 0.44375, while uniform controls remained uniform. This validates the finite method control, not a fitted model or a claim about GUI target positions.
- **Split-overlap mutation challenge:** `MUTATION_PASS`. A corrupted block assignment created one coordinate overlap; the auditor returned `HOLD_AUDIT_INTEGRITY` with the expected single reconstruction error.
- **Geometry feasibility:** The pinned OrbStack replication independently reconstructed 551 sites, but strict-interior support was only NW=6, NE=6, SW=3, SE=3, below the frozen minimum of eight per quadrant. The model T1 was not launched on that design. A preformal redesign screen did not establish the required geometry confound controls.
- **T1 allocation 02:** `HOLD_AUDIT_INTEGRITY`. The candidate's training update omitted the W1 gradient application while the auditor applied it; the reported base competence was also below the frozen 0.80 gate. This allocation does not adjudicate the hypothesis.
- **Corrected T1 v2:** Construction parity and the independent audit passed; ten models and 30,720 predictions were reconstructed with zero errors. The position-random arm accepted 1,218/2,560 positives (0.475781); spatial-block accepted 1,119/2,560 (0.437109). The absolute gap was 99/2,560 = 0.038672, below the preregistered 0.20 threshold. Both arms met the declared base-competence, false-accept, and block-support gates. This is a scoped failure of that threshold on one five-seed synthetic renderer, not an equivalence result.

The corrected result and its limits are documented in the [T1 v2 report](../../research/analysis/spatial_block_position_6590_t1_orbstack_v2/REPORT.md). The [T0 report](../../research/analysis/spatial_block_position_6590_t0_20261002/REPORT.md), [geometry feasibility report](../../research/analysis/spatial_block_position_6590_t1_geometry_feasibility_v1/REPORT.md), and prior #4752/#4814 evidence retain their separate outcomes.

## Boundaries

The random and spatial-block cohorts represent different interpolation/extrapolation envelopes, so the contrast is not estimator bias. No evidence here establishes production GUI spatial autocorrelation, real-layout robustness, safety, authority, user/model behavior, or product utility. Related #8544 asks about target–flanker spacing and target identity binding; human crowding is an analogy there, not a mechanism demonstrated by #6590.
