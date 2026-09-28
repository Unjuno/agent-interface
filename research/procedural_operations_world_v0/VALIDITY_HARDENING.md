# Second-round benchmark-validity hardening

This document records repairs selected from the adversarial review after the first shortcut hardening. It is instrument evidence, not model/controller performance evidence.

## Problems and repairs

### 1. Fixed task graph

**Problem:** every episode had effectively the same work script, allowing a Procedural-Operations-World-specific policy.

**Repair:** every episode generates a work-task subset and dependency graph. `work_task_count` controls subset size and `dependency_depth` controls graph depth. Station availability follows the generated graph and locked/completed stations are visually de-emphasized.

### 2. Fixed presentation grammar

**Problem:** watcher positions, station colors/icons, and visual layout were too stable.

**Repair:** `(seed, private family_key)` selects among 12 presentation families, watcher channel permutations/layouts, multiple active-alert palettes, seed/family-derived station colors/icon styles, map openings, and other procedural placement.

The private family key is only a nonce hardening mechanism. True held-out generator code remains a formal-evaluation requirement.

### 3. Public-generator / seed specialization pressure

**Problem:** hiding a seed alone does not prevent optimization to public generator structure.

**Repair:** generation now takes a separate evaluator-private `family_key`, included in `episode_hash` and revealed only in the evaluator report after execution. The key affects task/presentation/map generation. This substantially enlarges the generated family but is not treated as cryptographic isolation or a substitute for held-out generator implementation.

### 4. Controller action changed future alert questions

**Problem:** ACK timing used to reschedule the next event. Faster/slower paired arms therefore received different later alert timelines.

**Repair:** the complete alert schedule is generated before execution as absolute `(time, watcher)` events. ACK only changes current world state; it never mutates the schedule. The report retains the frozen schedule for replay.

### 5. Probabilistically unsolvable valid episodes

**Problem:** feasibility was based on expected Poisson event count, so a valid seed could fail to generate enough required events.

**Repair:** the event generator now schedules exactly `required_alerts` with bounded timing jitter and validates that the final deadline is inside the episode budget. Valid parameter configurations have a guaranteed generated schedule; generation failure is an explicit evaluator/instrument failure, never an agent failure.

A 10,000-seed audit of a boundary-like configuration produced 0 unsolvable schedules.

### 6. `event_rate` multiplied by `alert_burst`

**Problem:** increasing burst size increased both simultaneity and total arrival rate, confounding causal sweeps.

**Repair:** `event_rate` is now total alert arrivals/sec. Burst size groups arrivals at the same timestamp; inter-burst timing scales by `burst/event_rate`. Burst therefore controls simultaneity rather than multiplying the nominal total load.

### 7. Hidden scorer quota rendered to the agent

**Problem:** HUD displayed cumulative `alerts_acked/required_alerts` and target-hit progress.

**Repair:** numeric scorer quota/progress was removed. Visible alert state, station state, piece placement, and target sample remain legitimate world evidence. A framebuffer regression test changes hidden ACK/hit counters while holding visible world state constant and requires byte-identical images.

### 8. Recovery was mostly impossible to measure

**Problem:** many correctable mistakes terminated the episode immediately.

**Repair:** motor misses, bad terminal submit, and assembly placement miss are now bounded recoverable errors. `recovery_budget` is an independent difficulty parameter. Bad terminal input resets, misplaced assembly pieces return to their home coordinates, and a later valid effect records recovery. Wrong target, false alert acknowledgement, missed alert deadline, and instrument overflow remain hard failures to prevent brute-force search.

### 9. Concurrency was visually centralized

**Problem:** all watcher channels occupied one fixed top strip, encouraging one fixed scan routine.

**Repair:** presentation families distribute/permutate watcher channels among top rows, side banks, four-corner banks, or top/bottom banks. Pointer rendering and hit testing use the same episode-specific mapping. This does not yet create all desired heterogeneous async task types, but it removes the single fixed bitmap-scan geometry.

## Remaining attack surface

The following are intentionally **not** claimed solved by v0.2:

- a controller that can read benchmark process arguments/source/memory can still defeat secrecy;
- public generator algorithms can still be specialized to distributionally;
- a private nonce is not the same as post-freeze held-out generator code;
- synthetic success does not establish real-application transfer;
- a formal paired harness and B0/C1 accounting are still absent.

Those are evaluator/protocol gates, not reasons to make the world renderer heavier.
