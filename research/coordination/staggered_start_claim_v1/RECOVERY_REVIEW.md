# Recovery review: Issues #3946 and #3963

This branch restores all 18 source, plan, freeze, environment, STOP, and test
files from `research/staggered-start-claim-20260922` (two commits: the v1
freeze and the v2 batched successor). The original remote branch has no raw
formal bundle or final execution receipt. A bounded search of accessible
`/tmp` and Codex workspace file paths found no Issue #3946/#3963 output files.

## Immutable v1 STOP — Issue #3946

Issue [#3946](https://github.com/Unjuno/agent-interface/issues/3946),
comment [5766316269](https://github.com/Unjuno/agent-interface/issues/3946#issuecomment-5766316269),
records `STOP_EXTERNAL_EXECUTION_ENVELOPE`: 38 complete rows of a planned 54,
plus a partial 39th case; the outer command timed out and no execution/STOP
receipt or runner exit status was captured. The Issue reports a 38-row raw
SHA-256 of
`1651fc22a8a951e7dec2b5db826356552e91bc4630691b349bb990e3b398b8f8`, but those
bytes are not in the branch. The 38 rows remain incomplete and must not be
pooled with the successor or treated as a scientific failure/PASS.

## Reported v2 outcome — Issue #3963

Issue [#3963](https://github.com/Unjuno/agent-interface/issues/3963),
comment [5766438207](https://github.com/Unjuno/agent-interface/issues/3963#issuecomment-5766438207),
reports a separate 54/54-case allocation in nine batches, an independent
scoped PASS for `ATOMIC_CLAIM`, a separate baseline-policy FAIL, and passing
raw/database and batch audits. The reported raw SHA-256 is
`085cd8b7835d787841eaec679b86e219f2362d42f6846f4e7c18f9e2d32fa202`. The raw
bundle, batch receipts, database snapshots, report, and execution evidence
were not present on the recovered branch or found in the bounded local search.
Consequently, this remains an Issue-reported result, not a raw-byte-verified
result in this repository. Keep the full v1 STOP distinct; do not infer that
v2 completes or replaces it.

## Local checks and limits

The source/tests are preserved exactly; JSON parsing, Python AST checks, the
8-case v2 prefix-guard construction test, and workspace-index validation pass
locally. The guard test uses temporary synthetic files and invokes no worker.
The formal raw-dependent audit tests were not run because their required raw
outputs are absent. No formal runner, batch, worker, retry, resume, or
replacement was executed during recovery.

Neither this note nor the Issue comments substitute for the missing raw
outputs. Preserve the v1 STOP and v2 reported outcome as separate historical
records. No performance, production scheduling, exactly-once external effect,
or general agent-scheduler claim is made. Issues #3946 and #3963 remain open.
