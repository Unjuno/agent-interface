# Local CI record

Date: 2026-10-03. Checkout base: `52c42c40bb074f46db1dc74afb20508e68bc1282`.

The `analysis-index` workflow command list was executed locally, including the
frozen historical workflow-source restoration required by its geometry
provenance tests. On macOS, the workflow's GNU `sha256sum --check` step was
equivalently verified with `shasum -a 256 -c`; the frozen file hash matched.
The full listed construction-test suite completed without a test failure,
including both Issue #6645 T1 and T1b suites. The 17 analysis-index unit tests
also passed. The shell wrapper used for the second execution returned a final
status-assignment error after the test commands completed because `status` is a
read-only zsh variable; it does not indicate a test failure. The initial
execution against the current workflow source (without historical restoration)
did fail two geometry provenance tests, as expected from their pinned hash;
those tests passed after restoration.

Additional direct checks: T1b construction tests 5/5; analysis index contains
568 retained result/failure directories and is current; `git diff --check`
passed. Formal Docker allocation ran once per role (candidate and auditor),
with zero retries; no formal rerun was performed during CI.
