# Result — #1240 private-X11 GUI actor provenance

Decision: **PASS_MUTATION_ACTOR_X11_GUI_PROVENANCE_SCOPED**.

- Formal invocation: 1; reruns/replacements/tuning: 0.
- 360 formal cases = 9 frozen families × 40.
- Fresh injector children: 360; cleanup 360/360.
- Candidate vs independent actor oracle mismatch: 0.
- Lineage-bound non-self false self-credit: 0.
- Independent pixel scorer vs fixture visible-state errors: 0/360.
- Frozen 500 ms TEMPORAL_NEAREST false self-credit: 280.
- States: SELF_CONFIRMED40 / EXTERNAL_CONFIRMED160 / UNATTRIBUTED120 / NO_MUTATION40.
- Authority promotions: 0; task-success promotions: 0.
- Formal visible-change latency (descriptive): median 3.914 ms, p95 5.211 ms, max 15.410 ms.
- Formal fixture mutation latency (descriptive): median 2.360 ms, p95 3.514 ms, max 13.649 ms.
- Retained row digest: `6f2d76787826a25678a0768418234ab1bd6e362d94f6f5d8c8036f389f127075`.
- Independent retained-row audit: PASS.

The outer container tool reported a terminal-clear status after the runner finished, but the frozen formal runner exit code itself is retained as `0`; no formal rerun occurred.

Scope: this validates composition of visible GUI mutation evidence with fixed lineage-bound actor attribution in one cooperating private Xvfb/Tk fixture. HUMAN/OS are controlled injector labels, not authenticated real-world actors. This does not establish actor discovery in arbitrary desktop applications or production authority semantics.
