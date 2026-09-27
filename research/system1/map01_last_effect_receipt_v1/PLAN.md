# MAP01 last-effect receipt representation gate v1

Issue: #948
Base: `d303c98522c47cb35d0db511e05d26d29e91d85b`

## H
Adding exactly one caller-available typed feature family,
`last_effect_receipt = NONE | {action, extent, result}`, resolves every known
retained v30/v31 exact-prompt / distinct-teacher-label collision while preserving
all baseline source bytes and excluding current-image, future, evaluator-only,
and predicted teacher-label information.

## T
Retained-evidence deterministic audit only. Reconstruct the #937 held-out v31
collision and the development-known v30 collision from current-main artifacts.
Compare only baseline exact prompt bytes against exact prompt bytes plus one
canonical immediately-prior admitted-action/effect receipt. `UNKNOWN` is explicit;
no guessing. No model, GUI/game, OS input, training, threshold search, or live
allocation. One formal invocation after source freeze; reruns/replacements zero.

## D
PASS_LAST_EFFECT_RECEIPT_RESOLVES_KNOWN_COLLISIONS_SCOPED iff baseline known
collision groups reproduce exactly, every known collision becomes non-colliding
under the augmented signature, augmentation merges no baseline-distinct group,
and provenance/leakage/source checks pass.

HOLD_RECEIPT_NOT_RECONSTRUCTIBLE if the required prior caller-visible/effect
receipt cannot be reconstructed exactly for any collision row.

FAIL_RECEIPT_NOT_SUFFICIENT if any known collision remains after augmentation.
FAIL_INTEGRITY for source mismatch, hidden normalization, current-image/future/
evaluator/teacher-label leakage, post-result schema change, or formal rerun.

## C
Residual ambiguity may require temporal visual state, threat geometry, another
caller-visible event family, or may reflect stochastic / multiple-valid teacher
plans rather than missing last-effect history.

## U
Known small retained MAP01 cohorts only; exact teacher imitation is stricter than
task-effect equivalence. PASS does not authorize learner allocation by itself.

## Stop
One source-first retained audit only. If PASS, test the augmented representation
on a broader newly declared retained allocation set before RULE -> LINEAR -> TREE
-> TINY POLICY. If FAIL, add no second feature in this Issue.