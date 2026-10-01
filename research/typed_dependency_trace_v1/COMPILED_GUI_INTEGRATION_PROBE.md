# Existing compiled GUI v1 — state-scoped predicate acquisition probe

This is the first integration check after the typed-dependency discovery. It does **not** modify `compiled_gui_interface_v1.py`.

The current runtime calls the observation adapter with the interface's entire declared predicate list at each state. The retained Calc fixture declares four predicates:

- `document_dirty`
- `confirm_dialog`
- `save_target_present`
- `confirm_target_present`

This probe asks only whether the existing interface structure already contains enough information to derive a smaller state-scoped predicate request without losing branch/admission/effect dependencies.

## Derivation rule

For each state, include:

1. every predicate referenced by any branch condition in that state;
2. identity predicate + declared symbol dependencies for every possible action branch in that state;
3. expected-effect predicates of actions that can transition into the state.

Applied to the unchanged `calc-confirm-save-v1` fixture:

| state | all interface predicates | derived state-scoped set |
|---|---:|---|
| editing | 4 | `confirm_dialog, document_dirty, save_target_present` (3) |
| confirming | 4 | `confirm_dialog, confirm_target_present, document_dirty` (3) |
| done | 4 | `confirm_dialog, document_dirty` (2) |

No new semantic label is introduced; all dependencies come from fields already present in the retained interface.

## Finite correctness check

Predicate domains used by the retained fixture were enumerated:

- `document_dirty`: false / true
- `confirm_dialog`: absent / present
- `save_target_present`: false / true
- `confirm_target_present`: false / true

For every state and all 16 combinations (48 state-observation combinations total), compare full observation versus projected state-scoped observation.

Checks:

- selected/matched branch vector is identical;
- if an action branch matches, all target symbol identity/dependency predicates are present;
- all expected-effect predicates for possible incoming actions are present.

Result: **48/48 pass**.

This is a finite structural check of the current fixture, not live GUI correctness.

## Positive-path presentation size

For the retained positive state sequence `editing -> confirming -> done`:

- current full predicate fields presented: 12 total;
- derived state-scoped fields: 8 total;
- compact JSON predicate-object bytes in the fixture: 322 -> 206;
- compact JSON requested-predicate-list bytes: 246 -> 152.

These are serialization bytes and field counts only. They are **not model tokens**, not IPC measurements, and not an end-to-end latency result. Shared acquisition work may make actual savings smaller.

## Interpretation

The existing compiled interface already carries a potential dependency footprint in its branch conditions, symbol dependencies, identity predicates and expected effects. This means the next integration experiment does not require inventing a general dependency ABI first.

Candidate next change: an **adapter-side state-scoped observation request** for this one fixture, while leaving runtime admission/effect rules unchanged. A live comparison must verify that omitted inactive predicates do not hide a required invalidation and must measure actual acquisition/model-visible cost rather than extrapolating from JSON bytes.

## H / T / D / C / U

**H.** Existing compiled interface declarations are sufficient to derive a smaller per-state semantic observation footprint for the retained Calc method.

**T.** One retained interface, three states, 16 predicate combinations/state, structural branch/symbol/effect checks; no live GUI/model call.

**D.** PASS for structural coverage: 48/48. HOLD efficiency and live correctness claims.

**C.** A live adapter may have coupled predicate acquisition costs; an omitted predicate could matter through an undeclared application dependency not represented in v1; multiple branches/actions may enlarge the union.

**U.** One fixture only; no token measurement; no app I/O timing; no invalidation race; no generality claim.

## Next smallest experiment

Use the existing compiled Calc fixture with the observation adapter returning only the derived required predicate set. Compare against all-predicate acquisition under the same deterministic live task and scorer. Change no admission, action, effect, model, or task semantics.