# MAP01 last-effect receipt representation gate v1

Status: SOURCE-FREEZE / CONSTRUCTION PENDING.

This lane is the direct one-variable successor to #937. It tests whether one
caller-available `last_effect_receipt` feature family resolves the known retained
v30/v31 exact-prompt teacher-label collisions before any learner allocation.

The experiment is offline and source-first. It may read retained repository
artifacts and execute deterministic analysis in a disposable container. It may
not call a model/provider, run GUI/game input, mutate the shared runtime, train a
policy, tune thresholds after output, or rerun prior live allocations.

See `PLAN.md` for the frozen H/T/D/C/U and decision rule.