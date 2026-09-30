# Issue #5531 T4 preregistration — delay/correlation accuracy and completeness

Allocation: `fd5531-delay-correlation-20261001-01`
Branch: `research/5531-delay-correlation-v1-20261001`
Path: `research/verification/failure_detector_5531_delay_correlation_v1/`
Base main: `55c467786b3b98e5f8d1746f9c2970b7ada8b47c`
Related evidence: #5531 exploratory T0–T3 comments remain unchanged; this is a new stochastic timing/correlation rung, not a repeat or promotion of them.

## H / T / D / C / U

**H.** A typed `SUSPECTED_UNAVAILABLE` state with a two-independent-failure-domain crash-witness rule will reduce false permanent failure declarations on heavy-tailed healthy and partition/recover subjects compared with timeout-as-failure, while still detecting most actual crashes by tick 8. It will explicitly trade temporary admission holds for fewer false terminal declarations. Correlated observers on one host count as one domain, not two.

**T.** Use the exact stdlib-only frozen `experiment.py` and fixed seed schedule. Five synthetic subject classes: healthy-fast, healthy-heavy-tail, partition-then-recover, crashed, and explicitly restarted. Run 10,000 episodes/class under each of two policies, at fixed timeout thresholds 2, 4, and 8; threshold 4 is the sole primary comparison and the other two are sensitivity diagnostics. Horizon is 16 ticks. For every episode retain a SHA-256 hash-chain over status, suspicion duration, failure/clear ticks, and rejected late responses. Inject semantically invalid and stale-generation decoys at ticks 3 and 5. Two observers share host-A; a third is host-B. A typed crash decision requires host-A and host-B witnesses by tick 6. A valid same-generation response may clear suspicion but cannot clear terminal FAILED absent explicit restart.

Frozen delay assumptions: fast response Uniform{1,2,3}; healthy-tail mixture 0.75 Uniform{1..3}, 0.20 Uniform{4..8}, 0.05 Uniform{9..16}; partition response Uniform{3..12}+Uniform{1..3}; restart at tick 10 followed by Uniform{1..3}. For non-crashed subjects, host-A has a shared false-witness event with probability .04 plus its independent .005 draw when no shared event, and host-B false witness probability .005. For crashed subjects, host-A and host-B witness probabilities are .96 and .94. These are synthetic assumptions, not empirical claims.

**D.** Scoped method PASS only if the independent auditor exactly reconstructs all raw summaries/hash-chains; typed crash declarations by tick 8 are at least 8,900/10,000; at primary threshold 4, typed false final failures for healthy-heavy-tail are at most 10/10,000 and strictly below timeout-as-failure; all decoys are accounted for without clearing suspicion; terminal failure cannot be cleared by a late response without restart; and explicit restart plus a current response can recover. Any raw/audit mismatch, missed crash gate, unauthorized reactivation, or missing provenance is FAIL/STOP, preserved without rerun. Report suspicion-tick cost separately; it is not hidden by the accuracy metric.

**C.** A fixed timeout remains cheaper when delayed progress is worse than false terminal classification. Real detectors may instead need more domains, adaptive thresholds, trusted external witnesses, or no probabilistic decision at all.

**U.** Synthetic discrete delays and hand-set probabilities only; no real heartbeat, timing, observer independence, operating-system failure, GUI, authority, task-completion, or safety guarantee. Correlated/nonstationary faults and malicious witnesses are not calibrated. The tests do not justify deployment thresholds.

## Execution protocol

Construction suite is run once before freeze and must pass. Then read back and hash-bind the exact runner, tests, auditor, and this plan; freeze them in `FREEZE.md`. Invoke the formal runner exactly once from exact GitHub-readback sources using host CPython and `python -B`; after runner exit 0, invoke the independent raw-only auditor exactly once. Preserve every result. No tuning, retry, or replacement under this allocation. Docker/OrbStack is not used: current queue evidence authorizes only a separate #5156 lane, not this work. No model, GPU, network, GUI, or effectful action is used; the experiment is local deterministic CPU simulation.
