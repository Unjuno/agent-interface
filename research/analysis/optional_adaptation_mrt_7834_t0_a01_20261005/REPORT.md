# Issue #7834 T0 A01 — result

**Disposition: `PASS_METHOD_SCOPED`.** The one-shot exact finite candidate and the separate raw-only auditor each exited 0; retries: 0. The auditor reconstructed all 18 complete paths and 60 event rows, source hashes matched the pre-run freeze, and all five declared controls passed. This is the result for this allocation only.

## Result

The availability-aware known-propensity estimator returned `0.14999999999999994`; the independently recomputed exact potential-outcome oracle was `0.15000000000000005` (absolute difference `1.11e-16`, below the frozen `1e-12` tolerance). Both predeclared carryover-history strata also matched their oracle values within tolerance:

| Prior executed adaptation | IPW excursion estimate | Exact oracle |
|---|---:|---:|
| None | 0.12545454545454543 | 0.12545454545454549 |
| One or more | 0.29999999999999990 | 0.29999999999999993 |

There were six expected eligible opportunities across the two synthetic clusters. The deliberately history-ignorant, unweighted assignment contrast was `0.16044973544973545`; the executed-only contrast was `0.48664761904761883`. Both miss the aggregate oracle by more than the preregistered tolerance in this authored model. These are designed method controls, not estimated effects from user or live-interface data.

The synthetic distal episode endpoint moved in the opposite direction: success was 1.0 under paths with no execution and 0.0 under paths with any execution, while the proximal excursion effect was positive. The auditor retained these as distinct endpoints and passed the inversion control; it did not promote proximal improvement to task success. Mandatory-control snapshots were unchanged on every row and the reconstructed violation count was zero.

## Audit controls

- Zero-propensity history: classified `NONIDENTIFIABLE_ZERO_SUPPORT`; no estimate is accepted for unsupported history.
- Eligibility recorded after current assignment: rejected as `REJECTED_POST_TREATMENT_ELIGIBILITY`.
- Missing proximal observation: the corruption control sets the proximal value to null without deleting its event row; the complete-case reconstruction is rejected as incomplete instead of silently dropping it.
- Cross-session interference marker: rejected as `REJECTED_INTERFERENCE_VIOLATION`.
- Proximal/distal inversion: detected and reported separately as `DISTINCT_NON_SURROGATE_ENDPOINTS`.

The raw-only auditor rederived assignment paths and probabilities, outcomes, pooled and history-stratified IPW, both naive contrasts, distal outcome summaries, hard-control invariance, and source/raw identity. Its formal output reports zero raw errors and all five controls passed.

## Reproduction and integrity

- Base main: `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`.
- Freeze UTC: `2026-10-05T03:47:17Z`; source/freeze checks passed.
- Construction suite: 6/6 passed before freeze; the exact new PR-workflow test command was rerun locally after the formal allocation and passed 6/6; touched scripts compiled; `git diff --check` passed.
- Formal candidate: one invocation, exit 0; 18 paths / 60 event rows.
- Independent auditor: one invocation, exit 0; `PASS_METHOD_SCOPED`; retries: 0.
- Candidate raw SHA-256: `91e2a9bc12926533b8d3d7355d531cabbb7eef06af392bd4a752de828559d44c`.
- Audit JSON SHA-256: `24d8256e5821b0a88b49ca57f12124d429a4b2733b4bee4ac509f61b053f089f`.

Several post-run checksum attempts used the repository-root working directory even though the manifest entries are package-relative; those invocations failed on path resolution (one also named the package-local manifest as if it were at repository root). No inputs or outputs changed. Correct frozen-source and package-manifest checks from the package directory passed. The formal candidate and auditor were not rerun because of those command-path mistakes; the exact local CI construction step did run as recorded above.

The local `research/analysis/check_index.py` command exited 0 in the sparse checkout and reported that absent sibling directories were not treated as removals. The new package's generated-index entry is present; this is a sparse-scope check, not a full-repository index/Actions run. Full PR Actions remain the integration gate.

## Environment and limits

The source-frozen allocation ran on host macOS 27.0.1 arm64 / CPython 3.14.5 because OrbStack's containerd image store rejected both inventory and a pinned-image probe with `operation not supported` for content blobs. No container was created, and the shared daemon was not restarted, repaired, or modified. See `ENVIRONMENT.json`; no container isolation or resource enforcement is claimed.

This exact enumeration establishes estimator reconstruction under two authored session clusters and four decision points only. It gives no population interval, live proximal effect, actual user adaptation, GUI or task-effect validity, latency/savings, safety, or product result. A future prospective interface study still requires explicit consent, objective pre-assignment eligibility, known positive propensities, bounded carryover, independent distal scoring, and a separate authority gate.
