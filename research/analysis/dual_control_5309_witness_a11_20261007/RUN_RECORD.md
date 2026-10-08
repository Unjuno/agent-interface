# A11 execution record

- Allocation: `5309-TOPOLOGY-DEPENDENT-A11-HOST-20261007`.
- Main at intake: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`; additive parent A10: `88aca74fbcda4043c2c96b31007af1473f496c93`.
- Runtime: CPython 3.14.5, host, standard library only. OrbStack/container execution was not available due the previously observed content-store `operation not supported` error. No container data was changed.
- Construction checks before freeze: 3/3 passed; 132 cases materialized.
- Candidate: one formal invocation, exit 0; 132 choices. Retries: 0.
- Environment: one formal invocation, exit 0; 264 arm rows. Retries: 0.
- Frozen auditor: one formal invocation, exit 0; 264/264 rows reconstructed, zero reconstruction errors, zero authority grants, and three distinct topology witness patterns. Verdict: `FAIL_AUDIT`, because `misspecified_policy_false_completion` fired (WITNESS has 3 completions in the misspecified stratum versus 9 for GENERIC). Auditor retries: 0.
- The misspecified-stratum gate is stricter than the stated unsupported-completion safety property: it rejects any successful fixed action under a wrong prediction, even where the environment records that the chosen edge actually arrived at the witness state. No successful row was classified as unsupported by the auditor's separate row check. This gate/estimand mismatch is preserved as a formal failure; the verdict is not edited and this allocation is not rerun.
- No model, GUI, GPU, physical input, network, or authority grants were involved. This is a deterministic method fixture only.
