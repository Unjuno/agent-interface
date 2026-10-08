# #6576 timer-quantization support-cutoff sweep A03

## H / T / D / C / U

- **H:** On fresh synthetic seeds, at least one cutoff in {8,12,16,20,24} distinct observed q90-exceedance values will reject >=90% of baseline-eligible q=1.0 fixtures, while adding <=5% holds to continuous fixtures and <=10% holds to q=0.25 fixtures. q=0.5 is a prespecified intermediate arm.
- **T:** Fifty independent seeds per arm (q=0, 0.25, 0.5, 1.0), 4,000 observations each. Generate/hash all 200 inputs before candidate execution. Candidate reports existing gate decision and support-rule conditional rates for all five cutoffs. A separate raw-only auditor independently reconstructs per-fixture diagnostics and all aggregates from frozen input and candidate output.
- **D:** `PASS_CUTOFF_SWEEP_SCOPED` iff all arms have 50 fixtures and at least one candidate cutoff satisfies all three frozen conditional rates (q=1.0 rejection >=90%, q=0 rejection <=5%, q=0.25 rejection <=10%) with nonzero baseline-eligible denominators; report the smallest qualifying cutoff. Otherwise `NO_QUALIFYING_CUTOFF`. q=0.5 remains descriptive and cannot be substituted for a failed primary arm.
- **C:** Synthetic exponential scale 1.0 only; Python nearest rounding at frozen quanta; one sample size and finite cutoff grid. These cutoffs are candidates, not inferred universal constants. The baseline gate is the existing frozen #6576 block-median/correlation/exceedance diagnostic.
- **U:** No GPD/EVT/TailID fit, nominal p99 calibration, estimator coverage, real timer, physical release endpoint, hardware resolution, safety deadline, production threshold, or worst-case claim. Seeded synthetic independence is not evidence of stationarity/independence in operational traces.

## Freeze and execution boundary

Seeds 65761301–65761350 are used once per arm, with separate PRNG streams offset by `arm_index * 10000`. Each fixture has 4,000 exponential observations; nonzero q arms round to nearest q using the frozen Python generator. Candidate once; auditor once only after candidate exit 0; retries zero. Run only in the dedicated #6576 OrbStack VM's private Docker Engine with the pinned cached Python arm64 image, network none, read-only source/input/root, separated outputs, 1 CPU/2 GiB/zero swap. This is a separate construction allocation, not the formal six-case T0 and not the shared native-CI Engine.
