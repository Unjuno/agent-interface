# V39 pending-model invalidation construction A01

## H / T / D / C / U

- **H:** In the exact V39 loop, a hard health invalidation or incoherent health/ammo observation arriving while the planner future is still pending should interrupt the planner, cancel the renewable cover, require a verified empty release, and reject the eventual answer before action validity can proceed. A soft health change inside the authored envelope should preserve the cover and require ordinary fresh action validity after model completion.
- **T:** Execute the literal AST nodes for the current `while not future.done()` loop and the following `planner_result = future.result()` assignment from the frozen controller source. Use the production paired-signal monitor, cancellation helper, and final-admission helper with deterministic fake observations, planner future, and session process. Run hard-health, unknown-binding, and soft-change schedules once each in isolated one-CPU, network-disabled WSLc containers.
- **D:** PASS construction-scoped only if hard/unknown observations are consumed while the fake answer remains pending; interrupt precedes cancel; the empty-release receipt precedes late answer return; the returned answer is rejected with no input authority; and soft change produces no interrupt/cancel and remains `READY_FOR_ACTION_VALIDITY`. Any mismatch is retained as a construction failure; do not adjust after observing output.
- **C:** Exact current source branch and helper functions are exercised, but signal pixels, provider scheduling, GUI/X11, input backend, process termination, and live game timing are faked. This checks controller ordering under a declared schedule only.
- **U:** No live threat exposure, HUD extraction fidelity, real cancellation latency, physical release, useful feedback, bounded recovery benefit, ammo/progress effect, or MAP01 outcome is measured. This does not answer whether a real threat-linked HUD change crosses the authored guard before a slow answer returns.

## Frozen inputs

- Repository source commit: `d3a51bc4c962b223d05280225042b96a033df8bf`.
- WSLc image: `agent-interface/native-suite-wslc-a08:20261004`, image ID `sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a`.
- Candidate and auditor SHA-256 values and the two implementation source hashes are recorded in `FREEZE.json`.
- Execution order is candidate once, then an independent read-only auditor in a separate container. No retry; construction failures remain first outcomes.

See `results/pending-loop-a01/` for raw output and receipts.
