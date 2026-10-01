# Formal result — `FAIL_METHOD_SCOPED`

Allocation: `recovery-sentinel-5776-contrast-t0-20261001-01` (fresh Issue #5776 successor contrast; not pooled with or used to repair v1/v2).

## H / T / D / C / U

- **H:** Under the frozen repeated-probe synthetic queue fixture, final/first recovery duration would improve held-out gradual-loss sensitivity over the pointwise margin detector by at least 0.25, while both detectors stayed at or below 0.10 false alarms in every load stratum and the gradual-loss warnings led the planted loss by at least four ticks.
- **T:** Formal candidate ran once in a network-disabled, resource-bounded container on the pinned ARM64 image. It produced all 168 episodes (three loads × seven mechanisms × eight phase-distinct IDs), each with 100 event rows. The independent raw-only auditor ran once in a separate container, read-only against source and raw output.
- **D:** The auditor reconstructed all 16,800 rows with zero integrity errors (`PASS_LEDGER_SCOPED`). The frozen method gate failed: recovery-ratio false alarms were 3/16 (0.1875) in **each** load stratum, above 0.10; pointwise-margin false alarms were 4/16 (0.25) in the high-load stratum, also above 0.10. Gradual-loss sensitivity was 9/12 (0.75) versus 0/12 for pointwise margin, and the minimum counted warning lead was eight ticks. The prespecified result is therefore `FAIL_METHOD_SCOPED`; no threshold tuning, retry, or exclusion was made.
- **C:** The recovery-ratio detector falsely warned on the fixed demand-drift/no-loss mechanism (3/4 held-out IDs at each load); the high-load margin detector also warned throughout that mechanism (4/4). This deterministic authored fixture demonstrates a confound, not its prevalence in deployed workloads.
- **U:** No sampled deployment prevalence, predictive utility, production causal effect, safety, live-agent, or product claim follows. The experiment contains no live telemetry or probe-free comparison arm.

## Frozen-gate detail

Held-out set: 84 episodes; gradual-loss targets: 12; negative episodes: 48. The recovery ratio met the sensitivity and lead gates (incremental sensitivity `0.75`; minimum lead `8 >= 4`) but failed the shared false-alarm budget overall (9/48 = 0.1875) and in every load stratum. The comparator also failed the same budget at high load. Abrupt-breaker and spontaneous failures produced no gradual-recovery warning, consistent with the stated positive-control scope; they were not relabeled as gradual targets.

Candidate exit code: 0, one invocation. Independent auditor exit code: 0, one invocation, `PASS_LEDGER_SCOPED`, `errors=[]`. Formal retries: 0. The scientific gate failure is not an integrity failure.

Raw event ledger, stdout receipts, pre-run source hashes, guest/image identity and exact commands are retained in this directory; see `RUN.json` and `SHA256SUMS`.
