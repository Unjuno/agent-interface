# MAP01 workflow-owner history T1 (offline source-method experiment)

Status: pre-candidate plan. This is a CPU-only, no-network, no-Actions, offline
test of a proposed fail-closed pagination contract. It does not alter the
historical live-04 workflow or grant a MAP01/live allocation.

## H / T / D / C / U

- **H:** Removing the event filter is necessary but insufficient: a paginated
  workflow-run collector can safely expose the cross-event owner only when it
  rejects duplicate IDs, missing/truncated pages, inconsistent totals, and a
  page-cap exhaustion before asking the existing global-owner selector.
- **T:** Freeze current `main` and the exact live-04 workflow/helper sources;
  run a finite synthetic three-page response containing `push` and
  `workflow_dispatch` rows for the same workflow path; exercise pagination and
  URL-construction contracts; execute one candidate and a separate raw-only
  audit with five corruption controls.
- **D:** PASS only if the full history denies the later cross-event run, every
  incomplete/ambiguous view fails closed, and the independent auditor accepts
  the raw candidate while rejecting all five corruptions. Otherwise retain the
  first outcome and stop; no retries.
- **C:** Synthetic transport cannot establish GitHub API pagination behavior,
  consistency under concurrent run insertion, Actions concurrency semantics,
  or a real duplicate formal execution. It tests only the local collector
  contract against frozen examples.
- **U:** No live API/network, GitHub Actions dispatch, Docker/WSL, game, model,
  GUI/input, CUDA/GPU, or formal allocation. No MAP01 efficacy or safety claim.

## Frozen input and decision rule

The synthetic payload is a small, deterministic representation of the
cross-event counterexample already retained in #5953, plus unrelated workflow
rows. IDs and events are fixtures, not observed Actions runs. The candidate
must enumerate every page in the frozen payload, require stable integer
`total_count`, reject malformed or repeated run IDs, and reject short pages or
page-limit exhaustion before the final page count is met. The owner selector
then receives all rows for the workflow path regardless of event/head SHA.

## Execution ledger

Candidate, independent audit, and retries: 0 / 0 / 0 (before run).
