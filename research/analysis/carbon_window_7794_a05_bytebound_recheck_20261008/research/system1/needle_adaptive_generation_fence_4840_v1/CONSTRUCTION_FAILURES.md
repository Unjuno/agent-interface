# Construction chronology — Issue #4840

Before the formal freeze, Docker test invocation 1 ran 11 tests and returned three errors. `study.run()` tried to SHA-256 canonical JSON for a `NaN` confidence control; the strict serializer correctly refused non-finite JSON. This was an evidence-encoding/setup defect, not a scientific result or a formal run.

The nonfinite control was replaced with `confidence="0.99"`, a type-invalid but valid-JSON mutation. No hypothesis, stratum, pass gate or model behavior changed. The corrected construction suite then passed 11/11 in the pinned offline container. The original failure output is preserved in the task execution record; the formal freeze records the failure and correction. No optimizer/training updates occurred in either construction attempt.
