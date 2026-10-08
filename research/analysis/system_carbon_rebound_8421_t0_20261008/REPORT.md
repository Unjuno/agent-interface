# Issue #8421 T0 — result

## Disposition

`PASS_METHOD_SCOPED`. The frozen synthetic accounting ledger reconciled across three paired controls, the independent auditor recomputed every reported metric, and the pre-freeze test suite rejected all five frozen hostile mutations. Candidate and auditor each ran once with exit 0; retries 0.

This is only a method-contract result. Every energy, grid-factor, opportunity outcome, and embodied allocation value is synthetic fixture input. No client device, provider, model, GUI, user, or real emissions were measured. No claim is made that an interface route causes rebound or lowers environmental impact.

## Recomputed controls

| Fixture | Safe effects (reference → alternate) | Client J / safe effect | Session operational CO2e (reference → alternate) | Paired input-sensitivity interval |
|---|---:|---:|---:|---:|
| No demand change | 2 → 2 | 9000 → 5400 | 6 → 6 g | 0 to 0 g |
| Beneficial expansion | 2 → 3 | 9000 → 3840 | 6 → 4.3 g | -1.87 to -1.53 g |
| Seeded sign reversal | 2 → 3 | 9000 → 3840 | 6 → 9.1 g | +2.79 to +3.41 g |

The no-demand control holds safe effects constant and session operational emissions equal while client intensity changes. The beneficial-expansion fixture starts one additional safe opportunity and lowers the synthetic session total. The sign-reversal fixture has lower client joules per safe effect but higher complete-session operational CO2e, with the entire frozen factor-sensitivity interval above zero. These are authored arithmetic cases, not observations of demand response.

Allocated embodied CO2e is reported separately from operational CO2e under the frozen illustrative allocation; it is not a measured hardware footprint and is not added to the operational totals.

## Integrity and execution receipt

- Source SHA-256: `16f414e11cda213d34823e5f160799bbba5638aa7fe6a0f734092fc5b92a355e`.
- Raw SHA-256: `b4c8ec6a78ac337a0d0a1c28c8bac3c5f2b2262ed7ace8251531babbe8607e7f`.
- Audit SHA-256: `3e9beaa21de02ab9a20f72ec55afe6878b272ba983de933e5aa1097d6f10f48e`.
- Freeze commit: `ff4a8651108cd0da4e6e78e26d3b1ce961c2956b`; formal command counts and environment are recorded in [`formal_01/RUN.json`](formal_01/RUN.json).
- Preformal construction tests: 4/4, including 5/5 hostile mutations (energy omission, duplicate row, boundary relabel, denominator mutation, and grid-factor mutation).
- Host CPython 3.12.13, stdlib only. No container or isolation claim; Docker image/content-store access was not retried after the previously observed `operation not supported` failure.

## Boundary / next gate

T0 does not evaluate empirical route energy or emissions. The proposal's T1 remains gated on independent eligibility of #5702/#7728 workload, correctness, and energy sensor/provider-data inputs, plus a distinct frozen allocation. Missing provider or location/time data must remain `UNKNOWN / boundary incomplete`; this T0 must not be promoted to a real system-carbon estimate.
