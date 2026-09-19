# Causal-temporal history ranking: pre-model policy boundary (#2026)

## Disposition

**HOLD_PRE_MODEL_EVALUATION**

A deterministic nine-case policy evaluator was run once in an isolated Python process. It confirms the non-authoritative policy mechanics needed before a multimodal-model comparison:

- causal ordering can select an older action-linked observation over a newer irrelevant one;
- a false causal label is rejected by the evidence-validity filter;
- low-confidence/invalid evidence is not eligible;
- no valid evidence yields abstention;
- stale target identity does not override the current valid identity;
- an observation gap remains explicit in the case ledger.

Output digest: `c8fa24a49c75ca7b4c43a2071c98fde6f54840472821fba3e6762755ba1305a6`.

## Boundary

This is only a policy/oracle construction result. It used no multimodal model, GUI/X11, network, runtime, or task input. Therefore it does not answer the Issue's model-facing hypothesis, does not measure correctness, latency, input cost, or history inspection, and must not be promoted as a model result.

The equal-relevance case is retained as an explicit tie case; the no-effect case requires abstention. A follow-up model evaluation must use the same nine cases, fixed presentation across arms, and separate task correctness, causal-label compliance, false certainty, and evidence-use measurements.
