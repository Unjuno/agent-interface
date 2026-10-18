# A13 — one-call predicate lifecycle prompt check

## Question and frozen source

Does an explicit predicate-lifecycle clause make the same planner model produce a contract that the A12 guard accepts, while retaining target checks in pre-action branches and required exact field/save effects?

This is a single model-only construction call using one retained synthetic screenshot and token from #7422 R02 block-2/C/task-1. It is not a task replay or formal allocation. There will be exactly one provider attempt, with a 90-second timeout and no retry. The call cannot interact with GUI/input; tools are disabled and the sandbox is read-only.

Frozen checkout: `f57f7e9f7b74f8483ec372492be6f4f7c63b7353`. Model `gpt-5.6-luna`, effort `low`; Codex CLI `0.146.1`; the local catalog reports that model/effort as available. Input task record SHA-256 `80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64`; screenshot SHA-256 `dceef5c6abee047328d99007369db0fade828b26a02fb83ba931896ae818ed21`; output JSON Schema copied from the exact R02 grounding call `call-016`, SHA-256 `1b79d332398ea3e9d816c4982c441a34b4536a79d4fc0be2a9fac7457876d964`. Prior model answer SHA-256 `028eafd67c5bc075a7f412e89da75af13bbb3d833467f037e449033d3e225cf3`; the newly added lifecycle clause is fixed in `PROMPT.txt` (SHA-256 `8398ebec2581d05810dcbf3a39bf1389ffaf135edf25b62a8728bb6a2fa8d601`).

## H/T/D/C/U

- **H:** The added clause yields schema-valid output with no `target_valid` action postconditions, retains `target_valid=true` in action branches, and includes `exact_token_visible=true` for entry and `exact_saved_title=true` for submit/completion.
- **T:** Run the exact saved prompt once against the pinned screenshot and JSON Schema using the pinned model/effort. Apply the A12 candidate guard to the returned contract, then independently check branch and effect requirements plus bounded image coordinates/crop. Preserve CLI stdout/stderr, argv, provider answer, and usage if returned.
- **D:** PASS only if the single output parses, validates through A12, has both guarded action branches, correct action effects, correct complete effect, and a crop entirely within the 1280×800 image. Any missing/invalid output is retained FAIL/STOP; do not retry.
- **C:** One task-selected retained image, one seed/token, one model sample, and no actual GUI or scorer. Success cannot establish robust prompt compliance, correct visual grounding, or efficiency.
- **U:** Observer accuracy, actual effect, collateral/authority, all other tasks, transfer, setup cost, and end-to-end economics are unmeasured.

No success threshold may be changed after execution. This attempt does not modify or regrade R02.
