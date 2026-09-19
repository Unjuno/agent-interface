# V32 typed controller final admission

V32 integrates the shared final-action receipt into the live controller while
leaving v31 and its retained allocation hash-frozen.

After the planner future returns, v32 records the controller-observed terminal
time. It continues monitoring and releasing the active cover, then resolves the
planner terminal and any policy invalidation at one controller decision point.
This makes a hard event win before plan admission even when planner completion
won the protocol race.

Every normal outcome now carries `final_action_admission`:

- policy-invalidated output is `REJECTED_POLICY_INVALIDATED` and admits no plan;
- interrupted, failed, malformed, or otherwise planner-ineligible output is
  `REJECTED_PLANNER_INELIGIBLE`, is retained, and safely continues to a fresh
  decision instead of terminating the controller;
- schema-valid but controller-invalid semantics are
  `REJECTED_CONTROLLER_VALIDATION` and admit no input;
- a terminal game-state answer is `NO_INPUT_TERMINAL_STATE`;
- an active clean answer first becomes READY with no authority, then the first
  actual accepted primary plan record binds it to `INPUT_ADMITTED`.

The report counts these final statuses separately from planner turn statuses,
answer eligibility, model-action discard, policy invalidation, and executor
program counts. The receipt builders do not issue input, and an executor
acceptance remains the sole evidence that a plan obtained input authority.

Windows passes51 relevant tests and WSL/Linux passes34. V32-specific tests map
completed/eligible plus hard evidence to rejection, map clean completion to
READY, and bind a real-shaped first execution record to INPUT_ADMITTED. Shared
tests cover both terminal/hard orders, later revocation, terminal no-input,
validation refusal, malformed evidence, and the exact retained v31 race.

No v32 live allocation has run. The deterministic six-case path replay now
produces policy rejection, planner rejection, controller validation rejection,
terminal no-input, active admission and later revocation receipts. Four zero-
plan cases contain zero Executor acceptance; INPUT_ADMITTED contains exactly one;
revocation preserves one historical acceptance while current authority is false.
Windows and Linux output the identical SHA-256
`6c6bb063d3ed22fb9670a52a7a07b2212e9d027df3010170e2a5058964e4b9bc`.
Freeze a live v32 allocation only after source hashes and receipt/program audit
rules are committed.

That allocation is now preregistered, but not executed. It uses Luna-low, the
same v2 fixture as the trace that exposed the race, six decisions and one-run/no-
retry retention. Twelve source hashes and exact receipt↔program cardinality,
clock-order, aggregate-count and completed-terminal race criteria are frozen in
`map01_final_admission_v32_live_v1_prereg.json`.
