# Equal-policy focus projection comparison

The preceding pair failed its acceptance rubric and exposed ambiguous action labels plus unequal authority cues. This new cohort changes the question and source cases, so its results do not establish a causal improvement over v1. Both arms now receive identical explicit policy: historical target binding is separate from decision-time age; automatic tail replay and old lease reuse are prohibited; proposals require fresh runtime validation. Age greater than1000ms selects observe_only. Otherwise a known target binding proposes a new target action; unknown binding proposes focus recovery. These are supplied rules, not autonomous policy discovery.

focus_decision_view_v2 retains the entire terminal and latest matching observation, including unknown fields, rather than selecting individual fields. Earlier event history is omitted; full source replies remain authoritative. Duplicate/non-increasing observation sequences, mixed actions and observations after terminal are rejected. The preparer checked preservation of an added diagnostic field and three malformed controls before model calls. This is still a narrow lossy event view, not a complete receipt or validated generic parser.

Sources are a terminal reply from the second actual socket focus-fault run and the pause-review observations/terminal from actual newer-runtime construction. The latter is an extracted subset of runtime events, not a verbatim socket reply. All freshness values are synthetic decision-time metadata. Cases: unknown/fresh100ms, target/fresh100ms, target/stale5000ms. The target cases have completed terminals; the harder intentionally restored target with needs_decision from v1 is not independently revalidated by this cohort and remains a coverage gap.

Six real CLI calls requested the same Luna/low configuration, same working directory and arguments, with no tools/images. Order: unknown full/view, target fresh view/full, target stale full/view. All six returned exactly the eight expected fields, exited0 and had empty stderr. The audit checks frozen source/prompt hashes, stdin bytes, identical CLI arguments, raw-event arrival hashes and actual usage. No reruns were made.

| Case | Full input | View input | Reduction | Full/view output tokens |
|---|---:|---:|---:|---:|
| Unknown/fresh |12646|12258|388 (3.07%)|111/105|
| Target/fresh |13556|12170|1386 (10.22%)|105/110|
| Target/stale |13557|12171|1386 (10.22%)|102/104|

Cached input counts differ: unknown9984/9984, fresh1792/0, stale9984/9984 for full/view. Local CLI durations were6.472/6.008s,6.494/5.704s,6.838/8.564s respectively; the stale view was slower. There is no causal latency, billing, live model-receipt or broad reasoning claim. Actual served identity and full hidden context remain independently unverified. The pass supports compliance with these explicit rules on three static cases, not human-like live recovery.

Results: results/focus-model-pair-02. Prepare: prepare_focus_model_pair_v2.py. Audit: audit_focus_model_pair_v2.py. V1 failed results stay untouched. This is not default promotion. Next integrate a scoped view into one live decision boundary, retaining original evidence and fresh runtime validation; measure observation-to-planner-output-to-next-input time. Include intentional focus restoration with needs_decision and an actually measured stale observation before claiming recovery coverage. Do not continue static prompt sweeps merely to accumulate passes.
