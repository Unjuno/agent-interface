# Issue #5323 — causal attribution first unit T0

Status: a new, deterministic synthetic first unit. It does not modify or reuse prior experiment outputs.

## H / T / D / C / U

**H.** Separating causal identification from post-action association and from effect-linkage reduces false causal claims under known and hidden competing causes, while retaining an identified clean effect when evidence assumptions are met.

**T.** Freeze eight hand-specified event traces and five policies (40 rows): `POSTHOC_ASSOCIATION`, `TEMPORAL_LINEAGE`, `CONTROL_BASELINE`, `CAUSAL_MODEL`, and `UNKNOWN_ON_CONFOUNDING`. Traces cover a clean direct effect, no action/background effect, concurrent human action, hidden background drift, failed intervention with coincident effect, delayed observation after a pre-existing change, cross-target interference, and successful action with no effect. Run a deterministic no-model standard-library simulator once in an offline container, then run a separate raw-only auditor that independently implements the expected statuses. No live intervention, GUI, model, network, or external service.

**D.** `PASS_FIRST_UNIT_SCOPED` requires complete unique 40-row coverage; exact source-bound case digest; independent status/metric recomputation with zero mismatches; at least one false claim by the posthoc negative control; zero false identified claims by `UNKNOWN_ON_CONFOUNDING`; and retention of the clean direct effect. Otherwise report FAIL or STOP without retuning. `EFFECT_LINKED_UNDER_CONTROL_ASSUMPTIONS` is not counted as causal identification.

**C.** The event traces and ground truth are authored fixtures, not empirical data. `CAUSAL_MODEL` is supplied a completeness flag and truth for the synthetic oracle; this is an idealized comparator, not a deployable discovery method. The policies are deliberately small and not a production schema.

**U.** The unit cannot validate causal graph completeness, safe real-world randomization, hidden confounding prevalence, calibration, cost, latency, or whether an agent can author sound causal assumptions. It cannot establish task success, action authority, or product benefit. Positive scoped evidence only motivates a distinct held-out graph experiment.

## Frozen execution

- Base: `cf8ad3d1a675af9e64c1be356d03e35699548b33` (latest main fetched and branch rebased immediately before freeze).
- Branch: `research/causal-attribution-5323-t0-20260930`.
- Evidence path: `research/analysis/causal_attribution_5323_t0_v1/`.
- Runtime target: OrbStack Docker, cached image digest to be recorded from exact inspect; network none, read-only root/source, bounded CPU/memory/PIDs, dedicated output mount.
- Allocation: `causal-attribution-5323-t0-20260930-01`; runner once; separate audit once only if runner exits 0. No retries or output overwrite.
