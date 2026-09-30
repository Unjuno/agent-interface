# Issue #5531 T4 successor preregistration — delay/correlation metric repair

Allocation: `fd5531-delay-correlation-20261001-02`
Branch: `research/5531-delay-correlation-v2-20261001`
Path: `research/verification/failure_detector_5531_delay_correlation_v2/`
Frozen main: `29861fa860ad48bc47af68f2ebf330b1f5c9d842`
Successor to the preserved `STOP_AUDIT_REPLAY_MISMATCH` in #5554. The predecessor raw, auditor output, and sources are immutable and are not replayed here. This allocation uses a new seed base and a corrected metric contract.

## H / T / D / C / U

**H.** A typed `SUSPECTED_UNAVAILABLE` state with two independent failure-domain witnesses reduces false permanent failures on healthy heavy-tail/partition-recovery episodes versus timeout-as-failure while detecting most actual crashes by tick 8. It explicitly trades temporary admission holds for fewer false terminal episodes; observers sharing host-A count as one failure domain.

**T.** Same preregistered 5 classes, 10,000 episodes/class, thresholds 2/4/8 (4 primary), horizon 16, fixed discrete distributions, and scenario logic as documented in #5554's frozen `PLAN.md`, but new seed base 55310100. No source/output from the predecessor is used as a formal input. Compare typed suspicion against timeout-as-failure. Add three deterministic boundary probes to the raw result: (a) two-domain terminal witness followed by a late valid response without restart; (b) stale/semantically-invalid decoys without a valid response; (c) explicit restart followed by a current-generation valid response. Define `false_terminal_failures` consistently as **episodes that ever entered FAILED**, counted once per episode, not the number of transitions into FAILED. This is the exact metric-contract correction identified by source-only inspection of the previous auditor mismatch.

**D.** Scoped PASS only if the raw-only auditor exactly reproduces all summaries and hash chains; the corrected per-episode metric matches in both implementations; the deterministic probe bundle has exact expected outcomes (late response cannot clear FAILED without restart; decoys cannot clear suspicion; explicit restart/current response can recover); typed crash-by-tick-8 is >=8,900/10,000; primary-threshold heavy-tail typed false terminal episodes <=10/10,000 and strictly below baseline; all decoys are accounted; and audit errors are empty. Any mismatch or failed gate is preserved as STOP/FAIL without retry under this allocation. Suspicion tick cost is separately reported.

**C.** A single conservative timeout is simpler when a false terminal classification is preferable to delayed progress. If independent witnesses are not actually independent or trustworthy, this simulator's quorum result is inapplicable.

**U.** Synthetic timing/witness probabilities only. No real heartbeat, OS failure, observer independence, GUI, authority, task completion, safety, SLO, or deployment threshold is established. Correlated/nonstationary/malicious witnesses are not calibrated.

## Execution protocol

Run the construction suite once before freeze, then read back/hash-bind exact runner, tests, auditor, plan and construction result. Freeze these in `FREEZE.md`. Run the exact GitHub-readback runner once with host CPython 3.11.9 and `python -B`; only if exit 0, run the frozen independent raw-only auditor once. Preserve raw/audit outputs. No tune/rerun/replacement. Docker/OrbStack remains unauthorized for this allocation by the current #5085 owner-specific lease; local CPU-only is used. No model, GPU, experiment network, GUI or effectful action.
