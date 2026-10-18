# Issue #8434 T0 A01 — result

**Disposition: `PASS_METHOD_SCOPED`.** The finite authored simulator produced the preregistered route-rank reversal across temporal orderings while holding every sequence to the same 16 A / 16 B events, intensity, duration, and 32-opportunity horizon. The independent raw-only auditor reconstructed all 96 cases and accepted zero errors.

## Results

The paired contrast is `switch_reconfigure safe_effects − two_step_cache safe_effects`; positive values favor the first synthetic route. Held-out seed sets (12 seeds per structure) produced:

| Schedule structure | Median paired delta | Range | Direction |
|---|---:|---:|---|
| IID shuffle | −10 | −20 to −3 | two-step cache |
| Clustered, four runs of 8 | +21 | +21 to +21 | switch/reconfigure |
| Alternating | −31 | −31 to −31 | two-step cache |
| Held-out blocks, two runs of 16 | +27 | +27 to +27 | switch/reconfigure |

Calibration seeds reproduced the same sign pattern. The null route pair was identical on every case. All 96 schedules had exactly 16 events of each label and constant per-event intensity/duration; the auditor independently recomputed run lengths, transition counts, lag-1 product sums, per-event outcomes, denominators, and summaries. Forbidden-effect count and empty-release failures were zero by the frozen fixture oracle for every route/case. The five preregistered hostile input classes were rejected by the construction suite.

## Interpretation and limits

This demonstrates that the frozen analysis harness distinguishes route-law behavior under equal marginal exposure in this **authored finite model**; the ranking reversals arise from the simulator's explicitly defined reconfiguration and cache-expiry laws. It does not show that real disturbances are correlated, that Agent Interface has either route law, or that an IID benchmark misranks an actual controller. The 12 held-out seeds are deterministic fixture variants, not a statistical sample from a real workload; ranges are not confidence intervals.

No model, provider, GUI, game, OS input, physical release, or user task ran. This result does not establish performance, safety, human tempo, causal UI effects, or an operational route recommendation. Any T1/live transfer needs a separately authorized allocation and independent workload/ownership gates.

## Provenance

- Allocation: `DISTURBANCE-ORDER-8434-T0-A01-20261008`
- Freeze commit: `7487c226ed33bd4d5e622cbd2f88751c0e4107d6`; base main `6da5dc940fdb97866cfb900ca747edb8c94b2790`.
- Preregistration: [Issue #8434 comment 6051115798](https://github.com/Unjuno/agent-interface/issues/8434#issuecomment-6051115798).
- Candidate: one formal invocation, exit 0; auditor: one independent invocation, exit 0; retries 0.
- Execution: host Python 3.14.5, standard library, offline. OrbStack image-list preflight failed with containerd content-store `operation not supported`; zero container invocations and no isolation claim.
- SHA-256: SOURCE `21a4f077636f0a8848015c83f6681689e638c53201587b0452743bfe59c55493`; RAW `8abdffa4fc22ddb72bac5beec9cb093be762b1bcffdce429eb03af38a2848eab`; AUDIT `c364d973a09ef5819edb95042448bbdbfe11769fe5f53086ac711a25de3cfc0d`.

See `formal_01/RUN.json` for exact commands/exits and `formal_01/` for immutable raw and audit output.
