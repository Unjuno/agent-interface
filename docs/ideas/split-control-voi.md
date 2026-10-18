# Split-control value of information

- **Status:** Unverified transfer beyond the finite synthetic comparison
- **Source:** [#8638](https://github.com/Unjuno/agent-interface/issues/8638), related [#7934](https://github.com/Unjuno/agent-interface/issues/7934) and [#5306](https://github.com/Unjuno/agent-interface/issues/5306); A02 evidence in open [PR #8740](https://github.com/Unjuno/agent-interface/pull/8740)
- **Idea:** When one component gathers evidence and a different downstream component controls whether or how to use it, compare conventional information-value measures with net value after uptake, support, staleness, and decision consequences. This is an evaluation question; it does not grant evidence, action, or safety authority.
- **Outcome:** A01's candidate and auditor each ran once and produced an in-memory method pass, but the 48-row raw output was not persisted. It is an artifact-custody failure, not an auditable result, and was not rerun or reclassified. Separate A02 is `PASS_METHOD_SCOPED` on 12 synthetic profiles/192 rows: all three frozen A/B pairs ranked A above B by VOI-C and information-minus-acquisition-cost, but below B by split-control net value. Its candidate and independent audit each ran once; permission remained `NONE` and mandatory gates were unchanged.
- **Limits:** Host-only synthetic evidence after the proposed container inventory failed. No real planner uptake, GUI decision, task effect, safety, or product benefit was measured.
- **Next test:** Any transfer beyond the authored profiles needs a distinct authorized study that observes evidence uptake and downstream decision quality while preserving independent safety gates.

The source Issues remain authoritative for execution and status. See the [A01/A02 issue record](https://github.com/Unjuno/agent-interface/issues/8638#issuecomment-6068674543) and [A02 result PR](https://github.com/Unjuno/agent-interface/pull/8740).
