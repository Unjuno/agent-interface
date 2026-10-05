# V39 release projector rejects boolean retry ordinals

## Outcome

**PASS_METHOD_SCOPED** for the exact JSON integer type of a retry ordinal. On current main `19a6b723e58ccfd2b8265e88659589ef9223fcc9`, the frozen production helper accepted `true` as retry ordinal 1 and returned `measurement_ready=true`. A one-line exact-integer guard fixes this: ordinal must have `type(value) is int` and equal its one-based attempt position. The valid integer control remains ready; the boolean mutation now yields `measurement_ready=false` with no projected rows.

## Executed evidence

- `results/baseline-red.txt`: one pre-fix run of the focused regression, failing because the boolean mutation was incorrectly accepted.
- `results/focused-green.txt`: post-fix regression passes.
- `results/full-suite.txt`: all six projector tests pass.
- `independent-audit/audit-result.json`: separate exact-JSON-type adjudication; positive control and bool mutation both pass the narrow contract.
- `py_compile` and `git diff --check` pass on the modified helper and test.

## Scope

This is a synthetic schema-boundary finding. It does not test physical key release, native X11 state, application consumption, a game, model behavior, or the private live MAP01 allocation. It repairs one malformed-input acceptance defect in measurement readiness and does not establish the projector's overall correctness.

## Environment

The OrbStack Docker context was selected, but image inventory stopped before any container was created: containerd reported a missing content blob with `operation not supported`. Exact preflight output is retained in `results/orbstack-preflight.txt`. No image pull or engine repair was attempted. This narrow host-Python result must not be described as container validation.
