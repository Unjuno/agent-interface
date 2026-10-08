# T0 construction run record

- Issue: [#7466](https://github.com/Unjuno/agent-interface/issues/7466)
- Branch: `research/hazard-checkpoint-7466-t0-20261004`
- Frozen base: `0178fd24e9c317fff40e0fa1952fbe7e8ae01078` (`origin/main`, fetched 2026-10-04)
- Runtime: Ubuntu WSL2, Linux `6.18.40.1-microsoft-standard-WSL2-x86_64`, Python 3.12.3
- No Docker, GUI, OS input, provider, or task mutation was used.
- Commands, from repository root:

```sh
python3 research/analysis/hazard_checkpoint_7466_t0_20261004/sim.py research/analysis/hazard_checkpoint_7466_t0_20261004
python3 research/analysis/hazard_checkpoint_7466_t0_20261004/audit.py research/analysis/hazard_checkpoint_7466_t0_20261004/raw.jsonl
```

## Outcome

This is an exploratory simulator construction result, not the held-out calibrated study required by the Issue. Across 400 paired seeds per cell (2,400 raw rows):

| Cohort | Policy | Mean total cost | Mean lost work | Mean checkpoints |
|---|---:|---:|---:|---:|
| Informative | Fixed | 56.3525 | 18.2450 | 12.7025 |
| Informative | Event | 70.4875 | 8.3800 | 20.7025 |
| Informative | Adaptive | 79.8425 | 17.7350 | 20.7025 |
| Uninformative | Fixed | 51.9700 | 16.0525 | 11.9725 |
| Uninformative | Event | 67.5650 | 7.6475 | 19.9725 |
| Uninformative | Adaptive | 67.5650 | 7.6475 | 19.9725 |

The exploratory adaptive rule is strictly worse than both baselines in the informative cohort; its lower lost-work cost than fixed is overwhelmed by checkpoint overhead. In the uninformative cohort it exactly abstains to event-boundary behavior on all 400 paired seeds. Thus the fallback invariant passes, but the adaptive-benefit hypothesis fails for this deliberately simple construction. No policy promotion is justified. The result makes the checkpoint-cost accounting consequential rather than treating signal detection as a sufficient benefit.

## Independent audit and hashes

`audit.py` independently replays every seed/cohort/policy from the frozen schedule equations without importing the candidate, then checks the 2,400-row count, exact/unique keys, total-cost arithmetic, and event-fallback equality for all 400 uninformative seeds. Result: `PASS: 2400 rows; independent per-seed replay; exact cost reconstruction; uninformative fallback identical on 400/400 paired seeds`.

SHA-256 (Ubuntu `sha256sum`):

```text
sim.py      8d818d2b0962c104a6b3fcfe7bc93ea39bc4c936329c94de11db0371b0ffc611
audit.py    c044896f58099058a417418452424bf3e595638a79a4c9d675d856407d46de49
raw.jsonl   91dab9567c1332790660ac4736292dc8f36aa3b595535ff2a09cb90a13be26d0
summary.json ba305cc47a928620de7a8635c5dcc39f15eeb39edc87835cae2364e256b45818
```

The original Issue's predictive calibration, held-out distribution shift, effect-class correctness, and sensitivity criteria remain untested. Risks and scope limits are in [README.md](README.md).
