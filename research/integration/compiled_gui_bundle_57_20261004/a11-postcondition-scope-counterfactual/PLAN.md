# A11 — postcondition scope counterfactual

## Question and frozen source

Does removing the transient `target_valid` observation from the saved action's **post-action expected effect**, while keeping it as the pre-action branch/admission guard, let the archived R02 C block-2 task-1 trace complete its compiled graph when the independent saved-title predicate is true? Does the graph still yield when the saved-title predicate is false or unavailable?

This is a local construction counterfactual over retained evidence, not a replay of R02. It makes no GUI, input, provider, network, container, or allocation calls. It does not change any historical score or authorize a formal rerun.

Frozen checkout source is `88372bed99266ddfade7dedca9630555e18c8960`. Input task JSON SHA-256: `80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64`. The pinned compiled core is SHA-256 `d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014`; pinned planner contract schema is `c6b6ee14f9504c658e51128d35c150a830981c33773093ec01d4b83190271936`; pinned interface compiler is `3cfce9fbb9d85a0f425b49efd2e284e14f3358c69ff8226e82c80db30e8cc13e`.

## H/T/D/C/U

- **H:** The R02 contract failed after the exact title was saved because `target_valid` describes the current target check, not a durable post-submit property. Keeping it in the action branch and fresh admission, but removing it from that action's postcondition, will complete the same mock graph only when `exact_saved_title=true`.
- **T:** Source-pin and read one retained task record; compile its authored contract unchanged and with the one scoped removal; run the pinned core with deterministic callbacks reproducing the three recorded predicate states. Add two negative final-state controls (`exact_saved_title=false` and missing/unknown). Record all receipts and which callbacks ran.
- **D:** The as-authored variant must yield `effect_failed` at the archived final state. The scoped variant must reach `TASK_SUCCEEDED` only for saved-title true; both negative controls must safely yield and must not call the success verifier. Any other output is a failed counterfactual.
- **C:** This is a single task and synthetic callback sequence derived from retained runtime evidence. Manual contract editing bypasses model authorship and does not qualify the observer, independent scorer, runtime integration, task success, or efficiency.
- **U:** The interpretation of `target_valid` as a transient selected-target check is supported by the retained sequence but is not a cross-domain semantic type system. No uncertainty estimate or transfer claim is available.

No success threshold may be changed after execution. Raw and audit outputs will be separate; the prior R02 raw and disposition remain untouched.
