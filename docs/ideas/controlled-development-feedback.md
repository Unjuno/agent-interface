# Controlled development feedback for adaptive evaluation

- **Source:** Open [Issue #8072](https://github.com/Unjuno/agent-interface/issues/8072); finite synthetic A02 evidence is retained in open [PR #8394](https://github.com/Unjuno/agent-interface/pull/8394). A01 review and A02 package are under `research/analysis/controlled_feedback_8072_a01_20261005/` and `research/analysis/controlled_feedback_8072_a02_20261005/`.
- **Status:** A02 `PASS_METHOD_SCOPED` for its authored synthetic mechanism. No claim that real evaluator feedback changes researcher behavior, improves GUI generalization, or provides privacy.
- **Relation:** [#8319](https://github.com/Unjuno/agent-interface/issues/8319)/[#8327](https://github.com/Unjuno/agent-interface/issues/8327) study feedback channel crossed with candidate-update rule and saved-data audit. They are related follow-on questions, not substitutes for #8072's repeated-feedback policy comparison.

## Idea

Repeatedly exposing exact held-out task outcomes can let later candidate design adapt to a finite evaluation cohort. Compare full per-task feedback with a frozen, bounded aggregate-feedback rule, while always disclosing and vetoing exact hard safety/correctness failures. After candidate lock, publish all development and fresh-cohort raw evidence. This is an evaluator/development protocol, not a runtime control or permission to conceal evidence.

## Evidence and limits

- A01's candidate and raw artifacts are preserved, but its auditor did not compare the serialized feedback response with the independently expected response. Its apparent PASS is not accepted as an audit-qualified result; A01 was not rerun.
- Separate A02 fixed that gate and ran one candidate and one independent auditor invocation in the pinned, network-disabled container. The auditor reconstructed 100 paired seeds / 200 arm-runs with zero errors and rejected four planted mutations. It reported `PASS_METHOD_SCOPED`.
- In this authored generator, the median development-minus-fresh accuracy gap was 0.1172 for CONTROLLED versus 0.4375 for FULL; mean fresh accuracy was 0.8180 versus 0.5000. The advantage is substantially designed into the candidate/update rules (exact-ID patching versus transferable strata), so it does not estimate a realistic policy's benefit.

The A02 allocation is consumed. Preserve its outcome and do not rerun it. Any further test needs a distinct question and prospective freeze. This result establishes neither differential privacy nor a need to hide outcomes; complete raw evidence must remain available after lock. See the A02 [protocol](../../research/analysis/controlled_feedback_8072_a02_20261005/PROTOCOL.md), [report](../../research/analysis/controlled_feedback_8072_a02_20261005/REPORT.md), and [A01 audit correction](../../research/analysis/controlled_feedback_8072_a01_20261005/POST_RUN_REVIEW.md).
