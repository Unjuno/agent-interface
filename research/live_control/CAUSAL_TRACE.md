# Offline recovery evidence linkage

Issue #15 first experiment, using the unchanged actual-assistant
`servo-recovery-02` cohort. `causal_trace.py` exports source-line-addressed nodes,
typed edges, artifact hashes and unresolved questions. The frozen output is
`results/causal-trace-01/graph.json`. No runtime behavior or default interface changed.

The graph has 66 event nodes and 31 edges. Explicit source/expected sequence,
program IDs and lease deadlines provide links for declared observation bindings,
program acceptance, pointer admission and local feedback. Terminal-to-next-command
gaps are 7,712.513461, 11,138.762699 and 9,022.501981 ms, matching the earlier
boundary report. These include external planner/tool delays; they are not model
inference timings. The recorded final independent evaluation and saved SVG are
linked as evaluation evidence; this exporter does not replace the SVG scorer.

Five injected negative controls are rejected: nonexistent source, stale source,
wrong input deadline, input admission at expiry, and feedback assigned to another
program. They validate offline consistency checks, not live runtime prevention.

## What the six Issue #15 questions can currently establish

| Question | Evidence and gap |
|---|---|
| Image supporting each planner action | Expected observation resolves to a recorded PNG, including reuse. Actual model viewing is not logged here. |
| Authority for each input | Pointer admissions link to program acceptance and matching deadline. Complete key/release identity lineage is missing. |
| Feedback causing continuation/stop | Feedback references its observation and proposed command. Explicit proposal-to-execution IDs are missing; causality is not inferred from proximity. |
| Dominant planner gaps | Three terminal-to-command endpoints are mechanically extracted. Delivery-completion and model computation endpoints are absent. |
| Final task success | Recorded independent evaluation and hash of saved SVG are retained. Per-action physical effect attribution is unknown. |
| Failure retention | All original events remain source-addressable, including the false local goal. The final task succeeded after recovery; intermediate completion is not promoted to task success. |

Historical acceptance references stand in for authority records, not a newly
implemented shared authority ID. `observed_before` is deliberately different from
`caused_by`. The exporter does not prove input acknowledgement equals application
effect, historical observation equals present validity, or delivery equals ACK.

This development-known replay identifies instrumentation requirements before adding
speculation or live trace overhead. Next add explicit delivered-artifact references
and command/decision provenance at the real boundary, then measure serialization
cost and validate an unfamiliar recovery case. Token cost remains unmeasured.
