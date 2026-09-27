# Construction history — excluded from formal

## construction-01
First draft outcome: `FAIL_VOI_CORRECTNESS_REGRESSION`.
Weighted error was 0.05 for all three policies because an evaluation support-shift observation (`CHEAP=A`, then `ROI=A`) had zero likelihood under the development table, and the first draft allowed the empty posterior to fall through to an arbitrary terminal decision.

This was a contract/harness defect, not a formal scientific result. No formal invocation had occurred.

## construction-02
Repair before freeze: make zero development support after any observation a policy-independent `YIELD` condition; classify the held-out support-shift cells as required-YIELD rather than pretending their hidden L/R state remains safely decidable. No action cost, latency, development weight, non-shift evaluation weight, baseline order, VoI rule, or PASS threshold was changed.

Construction-02 outcome: `PASS_BOUNDED_VOI_SCHEDULER_SCOPED`.
Diagnostic metrics only (excluded from formal):
- FIXED_CASCADE weighted cost 4.32, latency 4.60, wrong0, required-YIELD error0, deadline miss0.
- CHEAPEST_FIRST same metrics.
- FROZEN_VOI_POLICY weighted cost 2.70, latency 2.86, wrong0, required-YIELD error0, deadline miss0.

These values motivated no further tuning. Source was frozen immediately afterward.
