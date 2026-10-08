# Issue #5424 T3 — freeze-induced selective labels

**Disposition: `PASS_METHOD_SCOPED`.** The frozen deterministic fixture demonstrates that a quiet-window rule can reopen an unrepaired route after three steps with no route execution, then expose it to severe outcomes. The independent current-generation probe rule does not reopen in the unrepaired, missed-signal, stale-signal, or common-cause cases; it does reopen after the one declared current-generation positive probe in the repaired case. This is only a method result for the fixture—not a real error-rate, safety, SLO, causal-benefit, or deployed-policy result.

## Frozen study and execution

- Allocation: `error-budget-selective-labels-5424-t3-20261001-01`
- Branch: `research/5424-selective-labels-t3-20261001`
- Frozen base: `49db21e330768800e8b3486203b70306f4e402f6`
- Candidate and auditor source read back from GitHub with exact Git blob matches before execution.
- CPython 3.14.5 on macOS 26.6.2 arm64; host-only, standard library; no Docker allocation was used or inferred.
- One candidate invocation: exit 0, 160 rows (5 scenarios × 4 policies × 8 steps), all 7 candidate gates true.
- One separate raw-only auditor invocation: exit 0, 160/160 exact reconstructed rows, no mismatches, all 4 frozen corruption controls rejected.
- Raw result SHA-256: `35a604ab5433ce92862ea946301e00451f366501923cf4505dedcc5ea87497d7`
- Audit result SHA-256: `a51da2891e42ba06cb0b4c61091c5d1c7bed75aef9763d21b7816a3f5911e926`
- Retries/replacements/tuning: 0.

## Key fixture outcomes

- `unrepaired_no_exposure`: `QUIET_WINDOW` made two unsupported unfreezes and exposed two severe primary outcomes; `AUTHENTIC_CURRENT_PROBE` stayed frozen with 8/8 primary opportunities censored.
- `repaired_current_signal`: the probe policy reopened only at step 5 on the matching authenticated generation and then observed three primary `OK` outcomes.
- `repaired_missed_signal`: the probe policy stayed frozen despite latent fixture repair, showing the liveness cost of missing evidence.
- `unrepaired_stale_signal`: the stale-generation positive did not reopen the probe policy.
- `common_cause_primary_fallback`: six severe fallback outcomes remained in the combined exposure count for every policy; route freeze did not make the correlated fallback safe.

`completed` in the raw summary is only the fixture's synthetic fallback/primary outcome and is not an independent task-effect oracle. Frozen-route potential outcomes remain explicitly separated from `UNKNOWN/CENSORED` policy observations.

## Decision and limitations

The result supports the narrow counterexample in H and the frozen method gates. It does not establish that a probe is genuinely independent, calibrated, complete, non-invasive, or safe to use in any application. The authenticated signal, route generation, repair state, task outcomes, and common-cause labels were fixture-authored. Probe false positives beyond the listed stale-generation case, non-stationarity, policy choice, user impact, and real fallback dependence remain untested. No production budget, runtime implementation, real route, GUI, user data, or action was involved. Preserve the prior #5424 T0/T1/T2 and PR #5438 artifacts unchanged.
