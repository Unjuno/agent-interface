# Issue #8581 T0 A03 — scoped synthetic result

**Frozen disposition: `BYPASS_DEFEATS_FEEDBACK_SCOPED`; independent audit integrity passed.** The candidate and raw-only auditor each ran once with exit 0. All four cells, 92 events, denominators, access events, hard-safety vetoes, lock/publication order, and scores reconstructed with zero errors; five of five frozen mutations were rejected.

All four cells selected candidate 5 and had the same development accuracy (17/24 = 0.7083), fresh accuracy (119/256 = 0.4648), and optimism (0.2435). The frozen decision rule uses `controlled/raw-bypass optimism >= full/sealed optimism`, so the equality meets its literal `BYPASS_DEFEATS_FEEDBACK_SCOPED` gate.

Interpretation is narrower than the label: because every cell is identical, this run does **not** show that raw-bypass availability caused an incremental change. Controlled/sealed also failed to show the preregistered advantage over full/sealed, so there was no advantage for bypass to remove. The result is a finite-method boundary outcome: this fixture did not demonstrate a benefit from controlled feedback, and the bypass arm was not distinguishable from the sealed arm.

The candidate did not read fresh labels; the independent auditor scored the fresh cohort after lock. The exact hard-veto event was disclosed in every cell. The auditor accepted benign documentation, distinguished denied and successful canary reads, recorded a no-attempt control, marked an unmonitored route `UNKNOWN`, and accepted publication only after lock. A01 and A02 remain separate immutable auditor/reconstruction failures; their data are not pooled with A03.

This is an authored deterministic fixture only. It does not establish real researcher behavior, real artifact leakage, validity or invalidity of historical results, absence of unknown channels, or a deployed-system/product effect.
