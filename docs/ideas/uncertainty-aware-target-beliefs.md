# Uncertainty-aware target beliefs and action admission — Issue #18

- **Status:** Parent #18 remains open and unverified as an integrated GUI/model capability. Two finite method contracts passed in separate scopes; neither demonstrates a live target belief, model-facing consumer, or successful application task.
- **Source:** [Issue #18](https://github.com/Unjuno/agent-interface/issues/18); exact-tie representation predecessor [#4146](https://github.com/Unjuno/agent-interface/issues/4146); action-admission successor [#4150](https://github.com/Unjuno/agent-interface/issues/4150); candidate-order successor [#7773](https://github.com/Unjuno/agent-interface/issues/7773).
- **Idea:** Preserve a bounded set of plausible targets, their source-bound evidence and uncertainty; admit action only when identity/freshness/margin gates pass, otherwise use a safe probe or return `NEEDS_DECISION`. A candidate set is not semantic truth or input authority.

## Evidence by layer

- **Ambiguity-preserving visual cue, #4146:** closed with `PASS_AMBIGUITY_PRESERVING_CUE_SET_SCOPED`. Across 48 authored byte-region cases, the exact-max candidate set matched an independent reconstruction in 48/48; all 36 tie cases retained fixture truth; authority grants were zero; raw-only audit errors were zero and 9/9 coherent corruptions were rejected. This establishes exact-tie representation on authored bytes only. It does not establish natural ambiguity frequency, detector quality, model benefit, task correctness, or production integration.
- **Admission contract, #4150:** remains open after ID003 `PASS_TARGET_BELIEF_ADMISSION_CONTRACT_SCOPED` over 64 authored score/provenance/probe rows. The rule had zero false ALLOW, compared with six deliberately incomplete top-1 false ALLOW cases; independent audit errors were zero and the frozen minimum of 10 coherent corruptions was rejected. Preserve its two predecessor outcomes: ID001 `STOP_LOCAL_SOURCE_MATERIALIZATION` and ID002 `STOP_SOURCE_INTEGRITY`; neither was rerun. Two of 12 attempted mutation controls were no-ops, so the harness was not 12/12 effective. The scores and safety labels are fixtures, not calibrated detector measurements.
- **Presentation-order consumer, #7773:** remains open at `HOLD_NO_CANDIDATE_LIST_CONSUMER`. Current-main source checks found no model-visible, identity-stable ordered target-belief list. The #4150 score-profile contract does not supply such a list. Tool-list order, detector-internal order, or image order would change the question and are not valid substitutes. No model, GUI, or candidate run occurred.
- **Parent evidence and refinements, #18:** the Issue body records a prior neighboring-rectangle mis-selection example and proposes unique/distractor/occlusion/freshness variants with independently scored target and collateral effects. The referential-repair and crossing/occlusion temporal-association comments are unverified proposals. They do not convert the two method results into an integrated outcome.

## Boundaries between related questions

The chain remains intentionally uncomposed:

1. #4146 preserves exact visual-score ties as a presentation cue, with no authority.
2. #4150 checks a synthetic admission rule over authored scores and provenance.
3. #18 requires a real, source-bound target hypothesis to reach a useful model/runtime consumer and then verifies the actual application effect.
4. #7773 can test ordering only after such an ordered model-visible consumer exists.

Passing a lower layer does not supply the missing consumer or validate the next layer. The parent remains separate from #5's general visual-address contracts, #7's view-set selection, and #35's cross-frame entity continuity.

## Next finite decision

Perform a read-only current-main and ownership check for one concrete path that can carry the #4146 candidate evidence into a #4150-style admission decision and a model-visible consumer. Record the source observation identity, candidate-set generation, freshness rule, authority boundary, and independent target/collateral oracle. If no such path exists, record the missing producer/consumer seam and keep the family parked; do not construct a proxy permutation experiment or consume a model/GUI allocation. If a consumer is found, freeze the smallest end-to-end task/effect comparison before any run, keeping safe refusal separate from successful completion.

## Limits and disposition

No result establishes calibrated uncertainty, lower wrong-object incidence in live use, safe probe behavior, model-visible utility, reduced planner work, efficiency gain, or general target identity. Keep #18 open. Keep #4150 open for its separate evaluation scope and #7773 open on its consumer-feasibility hold; do not close either based on this crosswalk.
