# Construction test harness repairs (additive provenance)

This package's source-level observation is distinct from the harness setup checks.

- Initial red attempt: generated wrapper AST was syntactically incomplete (`try` without `except`); the source path was not yet executed.
- Next harness attempts exposed missing factory bindings in order: `invalidation_monitor`, `index`, and the `json` module. Each failed before reaching the targeted renewal boundary.
- The repaired harness executed the frozen production `wait`, `submit_cover`, planner renewal block, and actual `ControllerFailureCleanup` implementation. The target observation/rejection scenario then passed as a characterization of the current-main failure behavior.

These harness construction errors are not game/runtime outcomes and were not relabeled as research results.

- First independent-audit launch pointed three parent directories above the repository root. The source/test record was unchanged; the audit root was corrected to the worktree root and the audit rerun.
