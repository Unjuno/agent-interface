# Issue #7728 Windows counter cross-check A02 preregistration

## H / T / D / C / U

**H.** On this Windows host, six consecutive one-second raw samples of `Energy Meter(RAPL_Package0_PKG)\Energy` will all remain monotone and inside an outer EMI v2 `RAPL_Package0_PKG` cumulative-energy bracket, with matching picowatt-hour units. This tests repeated raw-counter/EMI temporal compatibility beyond A01's single sample.

**T.** On current main, freeze the one-shot native Windows script, the reused byte-identical read-only EMI probe, independent auditor, synthetic controls, and local Windows SDK header hash. Read EMI once before and once after exactly six Performance Counter samples at one-second intervals. Also record paired total-CPU utilization samples to characterize ambient load; do not create load or launch any app, model, route, GUI, or task. Then run the raw-only independent auditor once.

**D.** `PASS_SIX_SAMPLE_COUNTER_ORACLE_MATCH` only if there are exactly six energy samples and six CPU samples; every counter status is zero and raw type is `NumberOfItems64`; all six energy samples have the target instance and are strictly monotone by timestamp and raw value; each raw energy value is between the same-channel EMI endpoints; EMI names the same target channel in unit code 0/picowatt-hours and its energy/time are monotone. Otherwise preserve the observed HOLD/FAIL. Negative controls must reject wrong unit, a nonmonotone or out-of-bracket sample, and a dropped energy row.

**C.** The direct API and performance counter could share an underlying Windows provider; agreement shows counter/EMI read compatibility, not independent physical calibration. High ambient CPU can make energy increments obvious and says nothing about idle operation.

**U.** This does not establish hardware resolution, a validated idle baseline, energy-boundary repeatability, process attribution, a GUI effect oracle, energy per effect, non-inferiority, or T1 eligibility. No controlled load or route is run. It is specific to this Windows host/OS and leaves the separate macOS HOLD unchanged.

## Stop rule

One candidate invocation and one independent audit only. No retry or follow-up sensor read to repair a result. No privilege elevation. A later task-level experiment requires a separate frozen protocol, controlled host state, and independent effect scoring.
