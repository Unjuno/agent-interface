# Issue #59 — allocation-global owner event/head invariance T0

## H / T / D / C / U

- **H:** A one-shot owner gate intended to be workflow-path-global can still admit a second run if the API request filters the run history by the current trigger event; head-SHA equality or difference does not repair a missing cross-event owner.
- **T0:** Freeze the exact live-04 workflow and the production owner helper from one current-main commit. Run an eight-row factorial: current event × prior event (same/different) × head SHA (same/different), plus a first-owner and a truncated-view control. Apply the actual event filter parsed from the frozen workflow query to the production helper; compare with the same helper receiving the complete workflow-path history. No Actions/API call occurs: all run rows are deterministic synthetic fixtures.
- **D:** `FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER` if all cross-event rows admit under the actual filtered view while the complete-history oracle denies them, same-event prior owners are denied, first-run admission passes, and truncated view is fail-closed. `PASS_OWNER_SCOPE_INVARIANT` only if no pre-existing same-path owner can be hidden by event/head dimensions. This is a source-composition counterexample, not evidence that a second real run happened.
- **C:** The exact query may be protected by workflow concurrency or launch timing not represented by the row snapshot. This fixture tests visibility/selection composition, not Actions scheduling, a lock race, or whether current workflow events actually overlap.
- **U:** No live API reachability, concurrency timing, workflow dispatch, container/game/model/GPU/GUI/input, release telemetry, or MAP01 efficacy is measured. The issue's previously retained cross-event, cross-head, and pagination findings remain unchanged.

## Frozen source and protocol

The source commit is `ad123c3875d81ebdc8bdfbdb59340005d705a60d`. The workflow query is parsed from the frozen `.github/workflows/map01-measurement-integration-live-04.yml`; the actual `select_global_owner` function is loaded from the frozen production helper by Git blob, then receives synthetic rows. The candidate never sends a request or dispatches Actions. Output writers refuse overwrite. Candidate and independent auditor run once after hashes and thresholds are fixed.

This successor combines the already retained cross-event and cross-head one-case counterexamples into a bounded factorial composition check; it does not amend or retry #5936, #5953, #5948, or #5969.

Execution environment: deterministic Python standard-library fixture only. Docker Desktop's engine was unavailable in this session, and this source-composition experiment does not need container isolation; no container was started or assumed.
