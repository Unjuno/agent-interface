# Formal failure — Issue #5428 T1 option-aware commit timing

Issue: [#5428](https://github.com/Unjuno/agent-interface/issues/5428)

Task: `ISSUE-5428-OPTION-T1-20260930`

Disposition: `FAIL_PREREGISTERED_MODEL_GATE`

Preregistration: [comment 5911326638](https://github.com/Unjuno/agent-interface/issues/5428#issuecomment-5911326638)

The audit of the frozen 2,304-cell candidate passed, but the predeclared primary decision gate did not. In the 1,152 costly-to-reverse/one-shot cells, the option-aware arm's mean regret relative to the exact one-step reference was 0; safety-only was `559/92160` (about 0.00607), and VOI-only was `401/30720` (about 0.01305). The required improvement was at least 0.05 against each. The measured improvements were therefore too small.

The option-aware arm is defined as an exact one-step lookahead over the model's actual post-probe action set, so its zero regret is by construction and is only an upper bound. It must not be presented as an implementable option-value estimator. The secondary gates passed: probe-induced primary-route loss was 3/1,152 = 1/384 (about 0.26%), and hard-gate violations were zero. They do not change the primary FAIL.

The independent exact-rational audit recomputed the factorial coverage, posterior branches, values, choices, regret, and deadline flags: `raw/audit.json` reports `audit=PASS`, `preregistered_model_gate=FAIL`, and `runtime_transfer=UNCERTAIN`. Four mutation controls were all rejected. The complete 3.2 MB formal raw record is `raw/formal.json`; hashes and execution identity are in [REPORT.md](REPORT.md).

This is a model-level result over authored priors, utilities, route survival, and probe accuracy. It does not establish human preference, calibrated option value, temporal hysteresis, live runtime effects, or production safety. No post-result tuning or candidate rerun is authorized by this record.
