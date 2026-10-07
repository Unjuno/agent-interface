# Issue #5749 source-routing comparator — A01 result

**Disposition: `PASS_METHOD_SCOPED`.** The independent auditor reconstructed all 18 rows with zero errors and rejected all six frozen corruptions. Candidate and auditor each ran once, both exited 0, and there were no retries.

## Findings

- With the same action-disagreement signal and query cost 2, worst-case regret 1 led the regret-cost policy to propose explicitly authorized default A, while regret 10 led it to CLARIFY. The source-router abstraction clarified both.
- At regret exactly 2, the frozen no-query tie rule proposed authorized default A.
- With low regret but no authorized default, the policy yielded; with high regret and no default, it clarified. No action was proposed without authorization.
- World-only uncertainty routed to VERIFY. Mixed world and preference uncertainty verified first under the regret-cost policy, whereas the source-router baseline clarified first.
- Unknown preference evidence yielded. All 18 rows had `authority_granted=false`.

This supports only the frozen finite decision-table distinction between consequence-priced preference clarification and the simple binary source-router comparator. It does not establish that either policy is better in real tasks. Utilities, costs and successful answer resolution were stipulated; no model, user, GUI, network, action/effect, safety, or transfer was tested. The comparator was inspired by—but does not reproduce—the PROUR learned policy or its evaluations.

## Execution and local checks

The pre-formal freeze is commit `3a4cdaa715`, based on `main` commit `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. The exact candidate and auditor stdout are retained in `results/formal01/`; hashes and runtime metadata are in `RUN_A01.json` and `SHA256SUMS`.

OrbStack was not used: current repository readbacks reported its bundled container CLI unable to inspect images (`operation not supported`). This small standard-library fixture ran with host Python 3.12.13 on macOS 27.0 arm64. Container and network isolation are not claimed.

- Package construction suite: 6/6 passed.
- Independent formal audit: 18/18 rows, 0 errors; mutation controls 6/6 rejected.
- `python research/analysis/check_index.py`: passed before adding this report; the generated index is refreshed in this commit.
- `git diff --check`: passed before report generation; rerun at final packaging.
- Full GitHub Actions workflow: not run locally or yet observed remotely; local checks above are not represented as full CI.
