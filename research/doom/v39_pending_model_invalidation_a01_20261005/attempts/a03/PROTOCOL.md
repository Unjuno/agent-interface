# V39 pending-model invalidation construction A01 — protocol freeze

## H / T / D / C / U

- **H:** In the exact V39 loop, a hard health invalidation or incoherent health/ammo observation arriving while the planner future remains pending should interrupt the planner, cancel the renewable cover, require a verified empty release, and reject the eventual answer before action validity proceeds. A soft health change inside the authored envelope should preserve the cover and require ordinary fresh action validity after model completion.
- **T:** Execute the literal AST nodes for the current `while not future.done()` loop and following `planner_result = future.result()` assignment from the frozen controller. Use its production paired-signal monitor, cancellation helper, and final-admission helper with deterministic fake observations, planner future, and session process. One each: hard-health, unknown-binding, and soft-change schedules. Run in separate one-CPU, network-disabled WSLc containers using the cached a08 image and a read-only source bind.
- **D:** PASS construction-scoped only if hard/unknown observations are consumed while the fake answer remains pending; interrupt precedes cancel; empty-release receipt precedes late answer return; the returned answer is rejected with no input authority; and soft change produces no interrupt/cancel and remains READY_FOR_ACTION_VALIDITY. Preserve any failure as the first outcome; no threshold adjustment.
- **C:** Current source loop/helper functions are exercised, but signal pixels, provider scheduling, GUI/X11, input backend, process termination, and live timing are faked. This tests controller ordering under the declared schedule only.
- **U:** No live threat exposure, HUD extraction fidelity, real cancellation latency, physical release, useful feedback, bounded recovery benefit, ammo/progress effect, or MAP01 outcome. It does not decide whether real threat-linked HUD changes cross the authored guard before a slow answer returns.

## Frozen inputs and attempts

Repository base: d3a51bc4c962b223d05280225042b96a033df8bf (tree f41871d5451e299a887c9c7d8ae6931118743cc2). Implementation and runner hashes are in FREEZE.json.

A01 stopped before candidate execution because WSLc could not resolve the host .git worktree pointer; see attempts/a01/STOP.md. A02 exercised the monitor/cancellation path but failed because the fake receipt clock preceded the production monotonic event timestamp; see attempts/a02/STOP.md. A03 changes only the harness clock source and uses a new output directory. Candidate and independent auditor run in separate containers. No retry within an attempt.
