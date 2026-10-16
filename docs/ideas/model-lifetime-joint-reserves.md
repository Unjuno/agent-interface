# Model-lifetime robustness of joint action and recovery reserves

- **Status:** Preliminary finite construction and post-result policy-space audit only; not `PASS_METHOD_SCOPED`.
- **Source:** [Issue #8873](https://github.com/Unjuno/agent-interface/issues/8873), successor to #8630 and #6580.
- **Idea:** Test whether one finite-horizon policy allocating observation, action, and recovery opportunities remains useful when transition-model uncertainty is session-sticky versus independently resampled each step.
- **Outcome:** A restricted 15-policy calculation and a later dynamic program over the full observable policy tree both preserve the toy discriminator: an action–recover–opposite-action policy has worst-case success 3/4 versus at most 1/2 for observe-before-action policies. The broader DP was post-result, not preregistered or source-hashed; no independent raw-only auditor or mutation suite ran. The disposition remains an audit-only synthetic analysis.
- **Boundary:** The independence law is stipulated by the toy kernel, not inferred for real interfaces. No empirical UI probability, runtime scheduler, safety, latency, or product claim follows.
