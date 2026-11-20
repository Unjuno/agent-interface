# A01 result

Disposition: `PASS_METHOD_SCOPED` for the strict scalar and execution-step discriminator; retain the v1 false accepts as the motivating counterexamples.

- Baseline: both v1 and strict candidate return `PASS/complete`.
- Five mutations: v1 returns `PASS/complete` for all five, including Python bool/int aliases and admission/execution step mismatch.
- Strict candidate: rejects all five with their frozen reasons.
- Independent auditor: `PASS`, six rows, all candidate results and frozen dispositions agree.
- WSLc candidate/audit/compile exits: 0/0/0. Focused host tests: 5 passed.
- Scope: synthetic contract behavior only. This does not show that any live producer emits the fields or that receipt timing reflects physical input or application effect.

The full repository pytest invocation did not collect: 66 errors involved missing/broken `PIL.Image` imports and modules/data omitted by the sparse worktree. See `COMMANDS.txt`; no project-wide green claim is made.
