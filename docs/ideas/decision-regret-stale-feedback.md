# Decision-regret exposure over stale-feedback windows

- **Status:** Scoped synthetic-method PASS.
- **Source:** [Issue #8528](https://github.com/Unjuno/agent-interface/issues/8528), successor to #6045 and #5986; merged evidence [PR #8547](https://github.com/Unjuno/agent-interface/pull/8547).
- **Idea:** Measure time-integrated decision regret caused by stale or misleading feedback while a relevant choice remains open, distinct from observation age and prospective causal benefit.
- **Outcome:** T0 A01 candidate and auditor each ran once; the independent audit returned `PASS_METHOD_SCOPED`, zero errors, and rejected 7/7 mutations. In the primary synthetic pair, visible rows and ages `[3,4,5]` were identical (age-only sum 12), while the toy unsafe exposure was 0 and the decision-regret integral was 0 versus 3. Controls preserved `UNKNOWN`/`NOT_APPLICABLE` rather than forcing a scalar where truth, clock, opportunity, or action-set assumptions failed.
- **Boundary:** This is a finite synthetic metric result. It does not show that earlier feedback causes improvement, assign real task value, or establish GUI/model/runtime or deployed-safety performance.
