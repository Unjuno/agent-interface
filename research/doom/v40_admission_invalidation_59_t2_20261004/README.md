# V40 cover-admission invalidation regression (T2, 2026-10-04)

## H / T / D / C / U

**H:** If an observation invalidates the current cover policy while the child acceptance event is already queued, the controller must stop admission, cancel the possibly accepted cover, verify empty input, and avoid starting the planner.

**T:** On the exact V40 candidate below, exercise both admission boundaries. For initial admission, feed the production wait/acceptance/cancellation helpers a FIFO of `observation(sequence=99)`, `accepted(id=cover-0)`, then a cancelled terminal with verified empty keys/buttons. For renewal while a planner turn is pending, use `sequence=101` and verify interruption of the matching turn plus cancellation/release of `cover-0-renew-1`. Run the focused V40 construction suite, compilation, and whitespace validation.

**D:** `PASS_CONSTRUCTION_REGRESSION` only if the observation monitor preempts acceptance, the initial path cancels before planner startup, and the renewal path interrupts the matching planner turn and requires a cancelled terminal with verified empty input. Any missing or unverified release fails the test.

**C:** A real child may reject stale-sequence submissions instead of accepting them. This injected sequence specifically tests the observed queue ordering and the required conservative cancellation after the acceptance might have occurred.

**U:** The test injects monitor output and child events. It does not exercise the child runtime, game, HUD parser, model, GUI, OS input, independent useful feedback, survival, or task success. The separate #59 live allocation remains unassigned.

## Change and evidence

V40 now passes its `ObservableSignalPolicyMonitor` into initial and renewal cover-acceptance waits. An invalidation during first admission triggers cancellation and requires a verified empty terminal before the loop can reach planner startup. Renewal admission invalidation uses the existing planner interrupt/cancel/release path. Decision accounting records `not_started` for final action admission when no planner turn occurred.

A separate read-only AST audit passes all six admission-path checks against the current candidate. The same auditor run against the exact V40 source from prior PR head `90b857e4ef1cf2d19b7560843da20723f7b4ad85` fails all six checks, including monitor forwarding and cancellation-before-planning. This negative control verifies that the audit distinguishes the prior path from the repair; it establishes source structure only. The construction suite now passes 10/10, including a renewal-boundary regression that observes planner interruption and verified empty release.

`RESULT.json` binds this result to the exact candidate, test, and audit-script SHA-256 values, base commit, environment, and commands. `test-output.txt`, `compile-output.txt`, `diff-check-output.txt`, audit outputs, and exit-code files preserve command evidence. The prior T0 record and T1 `FAIL_SOURCE_IDENTITY` result are retained unchanged; this result does not rewrite or supersede those historical records.

After this source change, the T1 read-only identity verifier was run again. It returned the expected exit code 1 and `FAIL_SOURCE_IDENTITY`: the candidate is now `0e1183a26cb0f816dcde97bb80f63f436ae306fd356a2ccef160e9ba5fe2add4`, while the preserved T0 audit and README still identify the earlier `961eadb2…` source. The output is retained in `identity-output.txt`; repairing that provenance gate remains separate from this regression result.

No live runtime or allocation was used.
