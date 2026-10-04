# Issue #7458 T0 A02 — clustered missed-feedback windows

## Result

`FAIL_REDUNDANT` for this finite simulator instance. The candidate and independent host auditor each ran once on the frozen A02 source. All 24 schedule rows were independently reconstructed. The held-out split contains 3 unsafe and 5 safe schedules; the training-calibrated max-misses-in-a-4-tick-window threshold is 2. It predicts all 8 held-out schedules unsafe (3 true positives, 5 false alarms, 0 false-safe), exactly the same decisions as the trivial always-unsafe classifier. Mean/p95 and freshness-age summaries are identical across schedules by construction and do not discriminate them. The proposed temporal feature therefore adds no held-out decision value here.

The first A01 construction with safety bound |x|>4.0 is retained in the sibling `clustered_missed_feedback_7458_t0_a01` directory; it had no unsafe schedules and could not test discrimination. A02 changed only the declared synthetic unsafe envelope to |x|>1.0 before its run. This is construction evidence, not a formal allocation or live result.

## Execution and scope

- Frozen source revision: `0db425b379f9438bf6b13c95dce1b763750b06d5`.
- Candidate: `python -B research/analysis/clustered_missed_feedback_7458_t0_a02/runner.py` (Windows host Python; exit 0).
- Independent auditor: `python -B research/analysis/clustered_missed_feedback_7458_t0_a02/audit.py` (exit 0; `PASS_AUDIT`, 24 rows).
- WSLc image list and image inspect both stalled on this host. The native run was used as a construction result only; WSLc portability is unverified. No image was pulled. No model, GUI, game, input, or #59 allocation was used.
- No claim about GUI safety, controller stability, useful model decisions, empirical latency, or #59 threat exposure.

## Reproduction

From the repository root, run the candidate then the independent audit using the two commands above. `FREEZE.json` defines the schedules, recurrence, disturbance trace, train/held-out split, feature and threshold selection before the A02 execution. `runner.py` emits `raw.json`; `audit.py` independently recomputes every schedule and output label and writes `audit.json`.
