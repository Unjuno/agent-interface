# MAP01 task-effect receipt boundary successor — T0

## Prior evidence and boundary

This additive T0 prepares a new measurement contract for the unresolved Issue #59 / #4193 boundary. It does not repeat a consumed game allocation. The authoritative prior first outcome remains `HOLD_ATTACK_TASK_EFFECT_NOT_REPRODUCED`: physical DOWN/UP was clean in 3/3 attack sessions, but plan-bound positive task effects were 0/3; NO_INPUT had zero actuation and zero effects in 3/3. The exact source result is `research/doom/map01_v12_attack_task_effect_live_v1/RESULT.json` (Git blob `5834667714297120a0a30f64a56e9ed196d47b0c`). No old effect time is imputed.

## H / T / D / C / U

- **H:** A unique source-bound receipt joining session, plan, actuation, physical event and independent scorer event prevents endpoint promotion from DOWN/UP alone. Missing or incomparable identity/time evidence remains HOLD/UNKNOWN.
- **T:** This T0 tests only a deterministic event-join contract on synthetic rows and corruption controls. It does not open a game, emit input, call a model, or consume an allocation. Live follow-up requires a separate freeze and explicit resource assignment.
- **D:** Construction PASS requires acceptance of one complete positive join; fail-closed HOLD for missing identity, wrong session/plan/actuation, incomparable clocks and absent source; rejection of duplicate/contradictory events and NO_INPUT attribution; and all frozen mutations detected. This cannot satisfy Issue #59's live threat/recovery gate.
- **C:** Synthetic integrity behavior is not efficacy, frequency, latency, physical occupancy, task usefulness, MAP01 completion or human tempo. #4193 and #443/#503 identities must never be replayed, altered or pooled.
- **U:** A new source-grounded live input-event identity, independently timestamped scorer endpoint, comparable clock attestation, matched conditions, bounded recovery/control policies and a fresh authorized Docker/GUI allocation remain necessary.

## Contract boundary

A formal row must join exact `session_id`, `plan_id`, `actuation_id`, `source_event_id`, `event_kind`, `event_monotonic_ns` and `clock_domain`. Positive TASK_EFFECT additionally requires exactly exactly one independently attested scorer event of type `KILL_COUNT_INCREASE` or `MAP_EXIT` after DOWN and before terminal, with `scorer_authority=false`. Physical release is not task effect. Programmed duration, changed viewport, HUD state transition, terminal publication and release receipt cannot substitute for scorer evidence. Missing joins are HOLD; contradictory duplicates are FAIL.

Before any live call, a new source-first preregistration must state the actual policy comparison (bounded recovery vs matched unauthored-coast/control), threat exposure, matched condition schedule, finite episode/time stop, event/raw retention, one-shot stopping rule, owner/resource lease and independent raw-only audit. Without explicit assignment, no Docker, GUI, model or input invocation occurs.

## T0 first outcome

Construction only: exact branch-saved source blobs ran on CPython 3.12.10; unit tests 10/10 passed. The bounded synthetic runner emitted 13 rows; a distinct CPython subprocess loaded the raw-only auditor without importing the runner/classifier and independently re-derived all 13 dispositions with zero errors. Seven corruption controls rejected (dropped case, changed verdict, wrong plan, authority escalation, timestamp mutation, unsupported effect kind, missing physical edge). Raw SHA-256 `69cfdc1ec3d00e86f0ccaa365d4b95aa752a48b874397cc0eaf6423f36508ba2`; audit SHA-256 `82f697950f94ffd8a3eaf0e9095b2ad5a2a00a6e9aff7df4e4b6d90ee3f7f3e2`. Decision: `PASS_CONSTRUCTION_T0_SYNTHETIC_CONTRACT_ONLY`.

This result is not a Docker reproduction or live effect/recovery evidence. Formal Docker/game/model/GUI/input calls: zero. The queue request for unrelated #5325 was not a lease and is outside this successor; no live slot is assigned. The issue #4193 predecessor HOLD is unchanged.
