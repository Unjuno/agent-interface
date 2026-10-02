# Issue #6604 T1 — retained MAP01 trace eligibility audit

## Disposition

**HOLD_NO_ELIGIBLE_TRACE.** This read-only audit does not find a retained #59 MAP01 trace that can identify a route-by-disturbance-timescale effect. It is neither a scientific failure nor evidence that a route does or does not benefit. Do not start T2 from v38/v39 or infer disturbance timing from screenshot cadence.

## H / T / D / C / U

- **H:** Existing #59 traces may contain enough provenance, held-input occupancy/release, independent effect, external target/disturbance schedule, and full route-cost evidence to support eligibility for #6604's T1 comparison.
- **T:** Read current-main published JSON artifacts only. Two MAP01 allocations were checked: v38 map01-v38-integrated-threat-live-01 and v39 map01-v39-coast-liveness-live-01. Parsed each retained report.json, runtime/events.jsonl, and planner-protocol.jsonl; no game, model, input, candidate, container, or auditor process was launched. Exact main observed at audit: afea9a530cafd7af529df4c9e59f36b816bca24f.
- **D:** T1 eligibility requires source capture/generation, actual held-input occupancy, an external target/disturbance schedule, release, an independent effect, and full route cost. Eligibility is conjunctive. If any required evidence is absent or non-identifiable, return HOLD_NO_ELIGIBLE_TRACE. Both allocations fail the external-schedule requirement: neither the retained runtime event records nor planner protocol contains a target-trajectory, disturbance-schedule, or external-target schedule record. Therefore neither run identifies the required exogenous disturbance strata. No route-by-timescale effect is computed.
- **C:** String/key absence in these three published JSON artifacts does not prove no such schedule existed outside the retained packet. The audit is limited to the main-branch bytes named below. It does not independently revalidate the original experiment's scientific conclusions.
- **U:** This audit does not establish live route efficacy, controller superiority, safety, gameplay success, latency benefit, or a T2-ready operating envelope. A future T2 needs a new prospective, source-bound external target/disturbance schedule and a qualified isolated fixture; old runs must remain unchanged.

## Evidence inventory

| Allocation | Report blob | Runtime events blob | Planner protocol blob | Runtime events / planner rows |
|---|---|---|---|---:|
| v38 integrated threat | d96b9032c7f55645dde20a1f95d916c943713914 | 02d65d49b61feadbdec2e051bd23d1ca845d5df1 | 48bc97f10507475df287d6e4c70358dfce52733f | 340 / 391 |
| v39 coast liveness | bff2459036dcdcc44ed100b0c0bc657e1bb8e69a | cbaeed9c7ba27b53cef9d10730ae33313371ad9a | c67e5c0fcefb8b1a3d690ae980f9ea25c45f6b23 | 634 / 985 |

The event-row counts and exact blob identities above were read from GitHub main. The matching check searched parsed event/protocol records for explicit target-trajectory, disturbance-schedule, external-target, and target-generation schedule fields; occurrences: **0 in both runtime event sets and both planner protocols**.

Other eligibility fields are present in scoped form:

- Source observations include image paths plus capture sequence/time and source-generation-style observation identities.
- Physical input evidence is present but uneven. v38 has 11 input_admission and 11 keys_held events; v39 has 39 admissions, 28 held receipts, and one input_released event. Existing release/cleanup evidence is preserved in the report/runtime records; this audit does not infer a complete per-key occupancy interval for every admission from these counts alone.
- Reports include visible-change effect receipts (pixel-scope) and post-control scoring fields, plus route accounting such as model/token/timing records. These do not supply the missing exogenous schedule.

## Reproduction

From a current checkout, fetch the six exact main-branch paths below as UTF-8 JSON/JSONL, verify the Git blob SHAs listed above, parse every JSONL row, and test all record keys/serialized values for the four schedule-field families above. Do not rewrite or rerun the original allocations.

- research/doom/results/map01-v38-integrated-threat-live-01/report.json
- research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl
- research/doom/results/map01-v38-integrated-threat-live-01/planner-protocol.jsonl
- research/doom/results/map01-v39-coast-liveness-live-01/report.json
- research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl
- research/doom/results/map01-v39-coast-liveness-live-01/planner-protocol.jsonl

This is a scoped, read-only eligibility audit—not the #6604 T2 experiment and not a MAP01 progress verdict.
