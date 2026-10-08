# Issue #8596 T0 A02 — exact chance-bound calculation fixture

**Disposition: `PASS_METHOD_SCOPED` / `H_SUPPORTED_SCOPED` for the frozen synthetic event models only.** Candidate and independent auditor were each invoked once on 2026-10-09. The auditor reported exact agreement, zero errors, and rejection of all seven frozen output mutations. This does not complete or validate the full Issue #8596 proposal.

At the four-opportunity deadline, the wide interval `[1/4,1/2]` yields exact reachability bounds `[175/256, 15/16]`; its illustrative midpoint is `3471/4096`, above the synthetic `4/5` threshold even though the robust lower bound is below it. The high interval `[1/2,3/4]` has lower bound `15/16`, above that threshold, while a miss path of mass `1/256` remains possible, so no universal finite sure bound exists. These are model-conditioned values, not measured probabilities.

The same-mean control reports mean delay 2 in both arms, but deadline-four completion differs: `1` for deterministic delay two and `9/10` for the distribution with a `1/10` mass at opportunity 11. The safe-trigger case keeps hard safety `PASS` while its progress lower bound `5425/8192` is below the synthetic threshold and selects `SAFE_YIELD`. Adding a reachable unsafe consequence changes hard safety to `FAIL` and the adversarial-worst progress lower bound to zero. The unknown-distribution case returns `NOT_IDENTIFIABLE` without a probability.

The fixture is an exact interval event model and does not synthesize or optimize a controller policy over the authorized-wait/observe/action states described in the issue. It does not validate a marker, delay distribution, rare-event rate, threshold, GUI observation, wall-clock deadline, safe action, task effect, or application. Therefore it supplies a narrow arithmetic and claim-separation result for a later MDP experiment; it is not evidence of computer-control performance, safety, reliability, or runtime admission.

## Custody and reproduction

- Freeze: `FREEZE.json`; source SHA-256 map covers nine preregistration and implementation files.
- Candidate raw output: `results/first-outcome/candidate.json`; output SHA-256 `3d91579f06465f8ef59698b094d87550cc6229bcd65a610157685ba38103aff7`.
- Independent audit: `results/first-outcome/audit.json`; stdout and exit code are recorded in `FORMAL_RUN.json`.
- First allocation A01 is preserved as pre-formal `HOLD_UNCERTAIN / INVALIDATED_PRE_FORMAL` in its own package; it had zero formal invocations. A02 is a new allocation and does not rewrite A01.
- Construction tests passed 8/8 in normal and optimized Python before freeze. No formal reruns or tuning occurred.
