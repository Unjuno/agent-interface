# Joint action/recovery reserves under model-lifetime uncertainty

These Issues share a finite-horizon allocation theme, but test different assumptions and have different evidence status. Keep their allocations separate.

## Joint observation/action/recovery budget — #8630

#8630 asks whether a finite horizon should jointly reserve opportunities for observation, task actions, and recovery. T0 A01 ran once on its frozen synthetic policy fixture and is `FAIL_METHOD`: the weak-signal case chose observation plus recovery (0.755) over no-observation plus recovery (0.750), contrary to the frozen gate. Candidate and independent enumerator agreed; preserve the first output without rerun or parameter adjustment. Draft evidence [PR #8744](https://github.com/Unjuno/agent-interface/pull/8744) remains open. No GUI/runtime/product result follows.

## Static versus changing transition regime — #6580

#6580 asks how the lifetime of an uncertain transition model changes no-authority continuation decisions. T0c, integrated by merged [PR #6597](https://github.com/Unjuno/agent-interface/pull/6597), is `PASS_METHOD_SCOPED` for its finite public-branch coverage gap: the independent auditor reconstructed 48 scenarios, 66 rows, and 6/6 controls with zero errors. This closes only that synthetic enumeration slice. WSLc reported unavailable swap-limit/cgroup enforcement, so effective memory enforcement is not claimed; the separate retained model-lifetime evidence remains `HOLD_MODEL_LIFETIME_UNIDENTIFIED`, and T1/T2 are not established. See the [T0c report](../../research/analysis/model_ambiguity_lifetime_6580_t0c_v1/formal_01_20261002/REPORT.md) and [Issue #6580](https://github.com/Unjuno/agent-interface/issues/6580).

## Joint policy under model persistence assumptions — #8873

**Status:** Open successor proposal with an additive post-result construction audit; not formally accepted.

#8873 combines the joint reserve question with two transition models: a session-sticky mode and a step-variable mode. Its preliminary 15-policy enumeration found a maximin success pair of `(1, 3/4)` for action–recovery–opposite-action, versus at most `1/2` worst-case success for observe-first policies under the authored model. A later dynamic-programming audit covered repeated observations and all legal horizon-4 choices and retained this numeric comparison, but the issue explicitly labels it post-result audit only: the DP is not source-hashed, no independently implemented raw-only auditor or mutation suite ran, and the probabilities are synthetic rather than GUI-calibrated. Preserve the narrower preliminary label; neither stage is `PASS_METHOD_SCOPED`. See [Issue #8873](https://github.com/Unjuno/agent-interface/issues/8873).

## Combined evidence boundary

The #8630 failure is about the frozen value comparison; #6580 T0c validates finite branch coverage but not the model-lifetime claim; #8873's added policy-space search is an exploratory completeness audit without formal integrity gates. These do not combine into an accepted scheduler, an action-authority policy, or a real-interface safety result.
