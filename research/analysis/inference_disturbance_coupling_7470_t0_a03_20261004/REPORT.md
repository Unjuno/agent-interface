# Issue #7470 A03 — circular phase sensitivity, seam-scope limitation

## Formal result

The frozen candidate ran once and emitted four unique circular rotations (eight trajectories); its independent raw-only auditor ran once after candidate exit 0, reconstructed every row, and rejected all three mutations. Candidate JSON SHA-256: `bc95a1d75f9697ab8181ead048279b2182bd47a5effd0121f7771e39ffbbed75`. Audit: `PASS_METHOD_SCOPED shifts=4 trajectories=8 null_states=1 phase_peaks=[8.0, 6.5, 6.0, 6.5] mutations=3/3`.

All rotations preserve the fixed latency multiset, disturbance sequence, 10-tick horizon, and within-stream circular order. Null trace is invariant `[0,0,1,3]`. In the planted plant the four phase peaks are 8.0, 6.5, 6.0, and 6.5; corresponding stale severity exposures are 20, 14, 12, and 14; outside-envelope counts are 1, 1, 0, and 1.

Post-formal descriptive statistic (not a preregistered gate): centered Pearson correlation between each rotated latency vector and fixed disturbance vector is 0.25, -0.05, -0.15, and -0.05. This confirms the phase contrast in this tiny finite sample, not an empirical association.

## Conformance boundary

A03 rotates intact sequences, but it simulates one period as a linear event list and does not execute the transition from the last event of a period into the first event of the next period. The Issue clarification explicitly requires the wraparound transition and its boundary effects. Therefore A03 is a phase-sensitivity method result for its declared one-period simulator, **not** full conformance to the clarified circular-boundary design. The frozen run remains unchanged; a separate successor must model at least two consecutive periods and audit the seam transition. A02 remains a separate arbitrary-permutation harness diagnostic.

## Scope

All interaction is planted by construction. No real inference latency, disturbance process, causal runtime relationship, prevalence, agent/game/GUI effect, safety boundary, human benefit, or deployment threshold is established. Host CPython standard library only; no container, model, GUI, network, GPU, or external effect.
