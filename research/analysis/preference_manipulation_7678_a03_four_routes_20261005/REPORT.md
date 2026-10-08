# Issue #7678 A03 four-route cache-context audit

**Result: `PASS_METHOD_SCOPED`.** The fresh A03 candidate and independent rank-vector auditor each ran once in the pinned, network-disabled OrbStack container; both exited 0, with zero retries. The candidate emitted all 6,624 unilateral-report rows. The auditor independently reconstructed every certificate with no errors and rejected all four frozen corruption probes.

The candidate's cache key now binds the complete evaluation case, including preferences, joint grants, protected constraints, and decision-maker identity. Construction tests reproduce the predecessor defect: the A02 preference-only key aliases cases whose grants, protected constraints, or decision rights differ. Under the corrected key, all 92 revoked-grant controls excluded route `d`, all 92 protected-constraint controls excluded route `c`, all 17 incomplete-comparison controls retained multiple completions, and the no-decision-right control selected nothing.

Across the 6,624 rows, 6,383 reports changed the certificate relative to the sincere report. The independent exhaustive utility analysis found zero safe-beneficial deviations under the declared possible-frontier set utility in both full-information and partial-information partitions. This is an exhaustive null only for this four-route fixture, selected information partitions, and stated utility.

The earlier A02 formal auditor startup HOLD and its context-insensitive-control finding remain preserved in [PR #7919](https://github.com/Unjuno/agent-interface/pull/7919); A03 neither rewrites nor upgrades that allocation. No claim follows about human manipulation prevalence, fairness, consent, privacy, GUI safety, production behavior, or general strategyproofness. No preferences are hidden and no choice is automated.

Raw candidate output, independent audit, run receipt, stdout, and checksums are in `results/formal_01/`. Construction regressions pass 4/4; analysis-index validation is reported separately in the PR.
