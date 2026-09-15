# Release-aware planner preparation v1

The client-wait v2 result exposes a bounded interval after physical input is
verified empty and before the prior program terminal arrives. This contract lets
a planner use that interval to prepare a candidate while preserving the later
terminal as a mandatory reconciliation boundary.

Preparation can begin only after the exact action-scoped, token-bound release has
been ingested. A prepared candidate is copied and deterministically fingerprinted.
It never grants input authority and cannot submit to Executor. After a matching
terminal arrives, the state becomes `PREPARED_REQUIRES_FRESH_ACTION_VALIDITY`;
the existing final-action-admission v2 boundary must still validate current
evidence and bind a fresh Executor acceptance.

Wrong-token or conflicting terminal evidence fails closed. The contract records
how much preparation overlapped the terminal wait without treating that duration
as useful work or a speedup. This is model-free construction. It has not yet run
an actual planner, reduced useful-action latency, or shown a token/task benefit.

## Frozen visual-planner allocation

The first live comparison uses the actual Inkscape fixture rather than an
artificial sleep. Both same-stream arms scan the same initial PNG inside a fixed
ROI, require one solid red rectangle, and prepare its exact bounding box, center
and click candidate. The early arm starts after verified release and separately
waits for terminal; the baseline starts only after terminal delivery. Both then
validate the target against the actual post-release PNG. No prepared candidate
is submitted to Executor.

Seed209, one allocation/no retry/model/cancel,34 source hashes and absent output
are frozen. Bounds require early fresh-validated readiness within200ms, at least
5ms advantage over terminal-first, and terminal-first readiness within300ms.
The exact expected target is bbox[596,373,643,408],1645 red pixels and center
[619,390]. Windows/WSL freeze verification and10 related tests pass. Run once
and retain the first outcome.

The allocation ran once and passed its frozen audit. Release was verified at
17.787ms and the early client returned at26.378ms. Early candidate preparation
completed77.638ms after focus request, before terminal at approximately110.755ms;
terminal-first candidate preparation completed139.137ms. After exact terminal
reconciliation and the same fresh-PNG validation, early useful readiness was
136.273ms versus164.592ms, a28.319ms advantage. Both arms produced the exact
frozen target and no candidate input was admitted.

Twelve files/266,171 bytes before retention receipt pass independent Windows/WSL
audits. This is evidence for one fixture-scoped visual preparation overlap, not
for model planning, executed task progress, token reduction, general speedup or
human-tempo operation. The next test must bind one freshly revalidated prepared
candidate to a new Executor acceptance and independently score its visible effect.
