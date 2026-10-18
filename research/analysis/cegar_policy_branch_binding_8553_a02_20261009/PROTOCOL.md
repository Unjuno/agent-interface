# #8553 A02 — observation-branch binding audit

## H / T / D / C / U

- **H:** The merged #8553 A01 auditor can accept a recovery policy whose observation branch values are unsupported by the selected safe predicate, or whose branches route observations to actions that fail in the frozen concrete fixture. Its `policy_safe` check examines `observation_features`, while the saved candidate serializes branch values in `observation`.
- **T:** Audit only the immutable A01 fixture and candidate output from current main. Compare the frozen A01 auditor on the unchanged candidate and two in-memory mutations against a new raw-only policy replay: (1) replace the two `p_color` branch signatures with unsupported values; (2) swap their child policies while keeping the signatures. Independently replay every retained CEGAR policy against the concrete finite transitions, using only selected, safe predicate observations. No candidate generation, GUI, model, network, user data, or action execution.
- **D:** `CONFIRMED_AUDIT_GAP` if the A01 checker accepts at least one mutated false policy, while the new replay accepts the unchanged A01 policy and rejects both mutations, with all five retained rows accounted for. `NO_GAP_REPRODUCED` if none of the two mutations passes A01 validation. `HOLD` for source/input hash mismatch, ambiguous transition/observation semantics, or incomplete replay.
- **C:** The two mutations are deliberately diagnostic and do not establish that the saved A01 policy itself was incorrect. A01’s original formal outcome remains immutable. A broader independent proof of recovery-policy synthesis is outside this audit.
- **U:** The result concerns only the authored deterministic fixture, its serialized policies, and these checker gates. It says nothing about real interfaces, safe live observations, recovery execution, or runtime/product behavior.

## Replay rule

At each policy node, every state in the current belief must expose the named action as enabled and safe. Its successor set is partitioned only by values emitted for the row's declared safe predicates on that action. Policy branch signatures must be unique and exactly cover those emitted signatures. Each child policy is recursively checked on its matching successor belief and remaining horizon. `GOAL` is valid only when all states in the belief are fixture goals. A missing branch, extra/unsupported value, unsafe action, or wrong route fails replay.

For the A01 fixture, the root `inspect` action emits `p_color` values `red` and `blue`; the candidate's `observation` fields hold these signatures. Following `red` must reach a policy that succeeds from `a`; following `blue` must succeed from `b`. Leaf actions return the designated goal/non-goal successors.

The A01 code and artifacts are copied byte-for-byte under `input/` and bound in `FREEZE.json`. The legacy checker is invoked only inside this distinct A02 diagnostic allocation, on the frozen baseline plus two in-memory mutated copies; its result does not overwrite or revise `input/audit-a01.json`.
