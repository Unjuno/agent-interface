# Issue #8421 T0 — frozen accounting-method contract

## H / T / D / C / U

**H (method hypothesis).** A correct ledger can show that lower client joules per independently verified safe effect need not imply lower complete-session operational CO2e when component energy and endogenous demand are accounted separately. The T0 fixture must preserve a no-demand control, a beneficial expansion, and a seeded sign reversal under fixed session duration and identical offered opportunity IDs.

**T (this allocation).** Deterministic, synthetic, offline accounting only. `SOURCE.json` freezes four offered opportunities per 60-minute session, two paired arms, one common versioned grid-factor input with declared bounds, and a separate illustrative embodied-allocation input. Activities include a failed attempt, retry, failure/recovery, and skipped opportunity; session rows include idle client energy and reserved provider capacity. The alternate arm in the two expansion cases also starts the fourth opportunity. Candidate materializes component rows and claimed summaries. An independently implemented auditor reads the frozen source bytes and retained raw, does not import candidate code, validates source/row identity and recomputes all reported values.

No model, device, provider, GUI, live task, or external effect is used. Every energy, carbon-factor, outcome, and allocation value is authored synthetic fixture data; it is not measured, calibrated, or representative. The fixed grid-factor range is a deterministic sensitivity interval, not a statistical confidence interval. Embodied allocations are illustrative and stay separate from operational emissions.

### Accounting contract

- Offered opportunities are the four exact frozen IDs. Started, failed, skipped, and `verified_safe_effect` counts are reported separately. The per-effect denominator includes only `verified_safe_effect`; it never silently becomes offered or started count.
- Every attempt, retry, failure, recovery, idle, and reserved-capacity row is included in session energy. Client and provider components remain separately reported.
- Operational CO2e (g) = total component energy (Wh) × grid intensity (g CO2e/kWh) / 1000.
- Client joules per verified safe effect = all client energy rows (including idle) × 3600 / verified safe-effect count.
- Allocated embodied CO2e and its per-effect value are computed from the separate declared allocation input and are not added to operational CO2e.
- Paired interval deltas use the same frozen grid-factor input across both arms. The auditor applies the low/high endpoints to alternate-minus-reference energy and orders negative bounds correctly. Bounds express only fixture input sensitivity.

### Preregistered controls and expected outcomes

1. `no_demand_change`: same dispositions and safe-effect count (2 each); reference/alternate total session energy 12/12 Wh and operational CO2e 6/6 g; client J/safe effect 9000/5400. The paired operational interval is exactly [0, 0] g.
2. `beneficial_expansion`: safe effects 2→3; total energy 12→8.6 Wh and operational CO2e 6→4.3 g; client J/safe effect 9000→3840. Alternate-minus-reference operational interval is [-1.87, -1.53] g.
3. `seeded_sign_reversal`: safe effects 2→3; total energy 12→18.2 Wh and operational CO2e 6→9.1 g; client J/safe effect 9000→3840. Despite lower client intensity, alternate-minus-reference operational delta interval must be strictly positive: [2.79, 3.41] g.

The three outcomes validate only that the accounting method distinguishes the stipulated cases. They do not estimate an actual rebound or beneficial environmental effect.

## D — decision

- `PASS_METHOD_SCOPED`: source/opportunity/activity identities reconcile; candidate summaries match independent recomputation; all five frozen hostile mutations below are rejected; and all three hand-derived controls reproduce the expected direction and bounds.
- `FAIL_METHOD`: any omitted/duplicate row, source/boundary/denominator/factor mismatch, arithmetic mismatch, or control-direction/bound failure.
- T0 does not decide `CROSSOVER_OBSERVED_SCOPED` or `NO_CROSSOVER_SCOPED`; those require empirical component coverage and are outside this allocation.

## C — competing explanations retained

This method fixture cannot tell whether real route changes alter work volume; additional tasks could be valuable; provider batching or utilization could lower marginal energy; grid/time and reserved capacity may dominate; or a real apparent reversal may be measurement noise or workload-order confounding. The audit is only as representative as the authored rows and declared boundaries.

## U — limits and stop boundary

One synthetic grid factor, one 60-minute accounting window, and three authored contrasts do not establish a real footprint, route effect, prevalence, optimal policy, lifecycle assessment, or climate benefit. No sensor, provider energy data, API key, hardware, GUI, live user data, WSLc lane, or policy change is authorized or needed. T1 remains a distinct eligibility/authorization gate requiring the #5702/#7728 workload, correctness, and energy-measurement gates.

## Freeze and execution discipline

1. Tests are construction-only and must pass before the freeze commit.
2. Freeze source, protocol, candidate, auditor, and tests with SHA-256 values in `FREEZE.json` before formal execution.
3. Candidate runs once, auditor runs once after candidate exit 0, retries remain zero. Preserve failed raw/audit/STOP output if either command fails; do not rerun under this allocation.
4. Docker/OrbStack was not used: the currently observed daemon has previously failed image/content-store access with `operation not supported`; do not repeat that operation here. This small stdlib-only method fixture is run on host CPython, with no isolation claim.
