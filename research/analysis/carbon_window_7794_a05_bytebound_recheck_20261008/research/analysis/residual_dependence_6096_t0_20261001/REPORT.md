# Issue #6096 T0 — subthreshold residual dependence sentinel

## Disposition

**`FAIL_METHOD_NO_ZERO_FALSE_YIELD_DETECTION_FRONTIER`.** In this frozen finite fixture, no tested lag-product threshold both detects the harmful phase-lag sequence before wrong continuation and maintains the preregistered zero-false-YIELD limit on valid periodic-motion/camera-jitter controls. This is a scoped method result, not evidence of a live defect or a safety guarantee.

## H / T / D / C / U

- **H:** A fixed-lag signed-residual dependence sentinel can stop before a separately labeled wrong continuation on a held-out zero-mean, pointwise-subthreshold sequence that pointwise and running-mean gates miss, without stopping matched valid-periodic/jitter controls.
- **T:** Three training traces set the calibrated threshold to one plus the maximum positive sum of the last five adjacent products (training maximum 3, trigger threshold 4). Seven held-out cases × five policies produced 35 decisions. Candidate received only `public.json`; truth labels were auditor-only. Policies were pointwise threshold 1/2, signed running-mean threshold 1/4, calibrated dependence, fixed four-sample hold, and always-YIELD. Candidate once; independent auditor once; retries zero.
- **D:** The auditor reconstructed 35/35 rows with zero errors. Pointwise and running-mean gates continued through the dangerous six-sample prefix, as hypothesized. The calibrated threshold 4 did not alarm by sample 8, while the first wrong continuation was labeled after sample 6. Lower thresholds 1–3 alarmed by sample 6 on the dangerous trace **and** on both held-out harmless traces with the exact same six-residual prefix (valid periodic motion and camera jitter). Thus there is no zero-false-YIELD detection frontier in this fixture. Mean-shift, missing-observation, and target-identity invalidation controls behaved as declared. No textbook Ljung–Box p-values were used.
- **C:** The matched prefix makes harmfulness unidentifiable from residual history alone at the decision time. Adding domain/phase/hazard evidence could change that; the fixed short-hold baseline observes earlier at additional observation cost. This does not show that every dependence feature is useless.
- **U:** Exact finite synthetic sequences only. No GUI, model, game, actuator, collision, human, or live safety result. The fixture does not calibrate serial-correlation false-alarm probabilities under adaptive sampling.

## Execution and scope

Source base: main `26f1da8f0a68cb256ea1b3623ef93b2cec4a0ef0`. Construction tests passed 6/6 before freeze. Candidate and auditor ran on Windows host CPython 3.12.10. Docker Desktop service was stopped; no service start was attempted because shared container ownership remains unresolved. No candidate/audit network, GUI, model, game, GPU, or physical-input calls occurred. This bounded CPU fixture did not require a container under the Issue T0 design; the deviation is explicit rather than claiming container isolation.

Raw decision record SHA-256: `94BFA905FCA8A72CAE2F4B5021449F05B3A70977A237AC10FBE630ECDAF10EB4`.

Independent audit SHA-256: `46097F97227B1A7667F41A8FF9B315AFDC30ED09B1382EDF7CA492FA5736385F`.

See `PLAN.md`, `FREEZE.json`, `RUN.json`, `public.json`, `truth.json`, `candidate.py`, `audit.py`, `raw.jsonl`, `audit.json`, and `SHA256SUMS` for the complete frozen method and evidence.

## Parallel-evidence chronology and qualification

Issue comment [#5933316110](https://github.com/Unjuno/agent-interface/issues/6096#issuecomment-5933316110) states the same hidden-transition indistinguishability boundary: equal source-bound histories can precede different latent outcomes, so a residual-only rule cannot distinguish the worlds. The Issue was updated at 2026-10-01 14:16 UTC; this allocation's raw was created at 14:21 UTC. The intake snapshot had shown zero comments, and the new comment was not re-read before formal execution. This is a coordination miss. The frozen data and gate remain unchanged; this execution must be treated as finite corroboration of an already-posted identifiability warning, not a novel independent discovery or external validation. The finite threshold frontier adds an executed quantitative illustration for this frozen detector/trace set. Any successor should retain indistinguishable worlds as a separate impossibility control, but exclude them from a positive early-detection criterion that presupposes observable discrimination; a primary efficacy case must contain a source-bound residual cue that differs before the wrong continuation.
