# Issue #5428 T1 — route-preserving commit timing

**Disposition: `FAIL_PREREGISTERED_MODEL_GATE`; runtime transfer: `UNCERTAIN`.**

This one-shot deterministic finite model tested whether explicitly pricing the action routes remaining after a safe probe adds enough decision value beyond safety-only and VOI-only policies. The independent exact-rational audit passed all 2,304 cells and the four corruption controls, but the preregistered improvement margin was not met. Preserve the formal failure in [FORMAL_FAILURE.md](FORMAL_FAILURE.md); retain every raw output under `raw/`.

## H/T/D/C/U

- **H:** An option-aware one-step policy will reduce expected regret by at least 0.05 utility units relative to both baselines on costly-to-reverse/one-shot cases, keep probe-induced primary-route deadline loss at or below 5%, and never bypass the hard gate.
- **T:** Exhaustive 2,304-cell factorial: four irreversibility classes; three bad-state priors; three probe accuracies; two wait costs; deadline slack, immediate alternative, post-wait alternative, primary-route survival, and hard gate each binary. Two latent states and both possible probe signals were evaluated with exact rational arithmetic. Formal candidate ran once in network-disabled OrbStack Docker.
- **D:** **FAIL.** On the 1,152 costly-to-reverse/one-shot cells, option-aware regret was 0 by construction of that arm as the exact one-step lookahead comparator; its improvements over safety-only and VOI-only were only `559/92160` (0.00607) and `401/30720` (0.01305), both below the preregistered 0.05. Probe-induced primary-route loss was `3/1152 = 1/384` (0.26%), within 5%; hard-gate violations were zero. Passing those secondary guards does not override the failed primary gate.
- **C:** VOI-only already had low regret on this authored grid. The apparent zero-regret option arm is a full-state one-step comparator and therefore establishes an upper bound, not a practical option-value estimator. A conservative HOLD policy or small calibrated/ordinal estimator may behave differently.
- **U:** Priors, payoffs, route survival, probe accuracy, and the one-step transition are authored. No human preference, temporal hysteresis, repeated noisy observations, live GUI/tool behavior, or production route availability was measured. This does not validate a runtime contract or any monetary interpretation.

## Observed actions

| subset | policy | primary commit | safe alternative | no-op | wait/probe |
|---|---|---:|---:|---:|---:|
| all 2,304 | safety-only | 960 | 144 | 1,200 | 0 |
| all 2,304 | VOI-only | 948 | 128 | 1,188 | 40 |
| all 2,304 | option-aware | 945 | 140 | 1,189 | 30 |
| high irreversibility 1,152 | safety-only | 432 | 96 | 624 | 0 |
| high irreversibility 1,152 | VOI-only | 420 | 80 | 612 | 40 |
| high irreversibility 1,152 | option-aware | 421 | 94 | 613 | 24 |

The option-aware route premium over the primary-only wait comparator was positive in only 18/1,152 high-irreversibility cells (zero in 1,134); the full grid had 24 positive cells. This is a narrow, synthetic operating region, not broad evidence that waiting is generally better. The VOI policy sometimes probes because primary-only information value clears wait cost even when routes change during the wait; the option-aware arm accounts for actual post-wait route survival.

## Frozen execution and audits

- Issue preregistration: [comment 5911326638](https://github.com/Unjuno/agent-interface/issues/5428#issuecomment-5911326638).
- Frozen base: main `c20193e9d75f06e46a5b78be0cfb31cd623eb080`.
- Formal invocation: one `docker run --rm --network none ... python /work/experiment.py`; exit 0; 2,304/2,304 cells; no RNG or candidate rerun.
- Runtime: OrbStack Docker Engine 29.4.0, linux/arm64; `python:3.12-slim`, image/repo digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Independent auditor: `PASS`, exact-recomputed all rational values/policy choices and all factorial cells; separately reports the preregistered model gate as `FAIL`.
- Corruption controls: 4/4 altered reports rejected (missing cell, closed-gate commit, forged regret, forged deadline-loss bit).
- Construction only: host/container syntax checks and one separately defined single-case smoke passed before preregistration. An initial shell redirection failed because `raw/` did not yet exist; Docker was not invoked in that attempt. The formal candidate then ran once after preregistration.

## Artifact hashes

| artifact | SHA-256 |
|---|---|
| `PLAN.md` | `9e2e5087597657ee34b16e214b971f6e59157c9b0d3970e0dbc0a0737265b06f` |
| `experiment.py` | `f8014cc789b6af54f6acb9bc8566d17a3119756fb01878f949f223410603c732` |
| `audit.py` | `3e7fbf1bf117f56c52a17dc96ec4f89826ff9131e2197055e5f0662f67a68c4f` |
| `smoke.py` | `3a911b9a4cdc50019f4805bd85cff6bf2ff03ab373fe18a6780f954e4a2d70f7` |
| `corruption_controls.py` | `80a0f39f6689bd46cef8872f8e9cbcd5c29b7e7232601bf6cea1895dd4c3805a` |
| `raw/formal.json` | `3d2e42aee2c5deca1a65c8f1ba69db51ea85b54496e754198650603cae2ea7b4` |
| `raw/audit.json` | `0f1bea3054eeaefa74d229fbe5ad667f9f4ca56b0a0a04e69f50c3c6d22a7f93` |
| `raw/corruption_controls.json` | `8bdeb7162cb71a5935e7d58f3e1bd32547a04aa5f8de8d47fdeb80a6d9e89f7e` |

## Safe continuation boundary

Do not retune or rerun this frozen T1 grid. A successor may separately preregister a genuinely implementable ordinal policy and hysteresis under sequential noisy observations, with the exact one-step model retained only as an upper-bound comparator. It must preserve this failed result unchanged and test whether the policy can estimate route survival without access to the simulator's hidden state.
