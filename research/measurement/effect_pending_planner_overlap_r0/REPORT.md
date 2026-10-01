# Effect-pending planner overlap analytical R0

Issue #1616. Analytical-first composition study; no GUI/X11/model/provider/network/task-input allocation.

## Decision

`PASS_EFFECT_PENDING_PLANNER_OVERLAP_MODEL_SCOPED`

The finite event contract supports a client-visible **verified physical release / TASK_EFFECT pending** state without granting input or semantic authority.

A planner/client may resume reasoning after one verified matching empty release while:
- `current_input_authority=false`;
- `new_input_admissible=false`;
- `semantic_authority=false`;
- TASK_EFFECT remains separately `pending`, `resolved`, or `unresolved`;
- terminal remains an orthogonal lifecycle fact and never implies TASK_EFFECT.

## Exhaustive result

Candidate: incremental state tracker.
Oracle: independently structured whole-history classifier.

Event alphabet8:
- matching verified RELEASE;
- wrong-token RELEASE;
- matching current no-authority TASK_EFFECT;
- wrong-token TASK_EFFECT;
- authority-escalating TASK_EFFECT;
- EFFECT_TIMEOUT / UNRESOLVED;
- matching TERMINAL;
- wrong-token TERMINAL.

All traces of length0..5 were enumerated: **37,449** total.

Results:
- candidate/oracle mismatches: **0**;
- invariant violations: **0**;
- corruption controls: **5/5 rejected**.

The valid-state space includes:
- release verified / effect pending / terminal pending;
- release verified / effect resolved / terminal pending;
- release verified / effect unresolved / terminal pending;
- effect-before-release states that do not make the client resume;
- terminal-without-effect states that remain effect-pending.

Invalid lineage, effect authority escalation, duplicate effect, and effect-after-timeout fail closed into `needs_reconciliation`.

## Integrity

The first deterministic exhaustive result was executed once in the container. It was not regenerated after publication. Exact source/result bytes were then frozen on the branch and Git-blob readback matched local `git hash-object` for PLAN, candidate, oracle, exhaustive runner, corruption runner, audit source, RESULT and CORRUPTION 8/8.

The independent retained-result audit was executed once **after** that exact remote readback and returned PASS with expected trace count37,449 and errors[].

## Boundary

This proves semantic composability only under the declared totally ordered event contract.

It does **not** prove:
- runtime stream reliability;
- concurrent delivery/reordering behavior;
- clock/deadline behavior;
- real XTerm latency benefit;
- permission to execute new input after release.

The important separation is: **planner reasoning may resume; input authority does not.** A future live transfer must still use a separate fresh admission path before any new motor action.

## Next empirical discriminator

One fresh XTerm/client comparison should compare:
1. blocking task-effect handback; versus
2. early client return at verified physical release with state `PHYSICAL_RELEASED_EFFECT_PENDING`, followed by later TASK_EFFECT reconciliation.

Both arms must keep new input authority false until a separately validated future admission. The test should measure planner/client idle time and retain effect/terminal reconciliation independently.
