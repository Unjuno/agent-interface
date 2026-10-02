# Issue #59 — cross-event allocation-owner counterexample

## H / T / D / C / U

- **H:** The live-04 launch guard is not allocation-global across GitHub event types because the workflow queries runs with `event=$GITHUB_EVENT_NAME`. A `push` run and a `workflow_dispatch` run using the same versioned workflow path and allocation ID can each receive a singleton view and both be admitted by the otherwise path-global helper.
- **T:** Freeze current main and replay the exact live-04 helper against the actual retained push run plus one explicitly synthetic `workflow_dispatch` row. For each current run, reproduce the workflow's event-filtered API view and call the helper once. An independent oracle counts admissions across the fixed path/allocation, ignoring the event partition.
- **D:** The counterexample is present if each per-event call returns `PASS_CANONICAL_GLOBAL_OWNER` and `may_enter_formal_step=true`, while the independent invariant counts more than one admitted run for the same path/allocation. The control passes if the total is at most one. No GitHub Actions dispatch will be issued.
- **C:** Deterministic local Python composition test using the exact current-main workflow and helper plus one synthetic dispatch row. The dispatch is a reachable trigger/configuration, not an observed second execution. This demonstrates a source-level guard gap, not an actual duplicate formal run or a race.
- **U:** No live dispatch/API visibility/pagination/concurrency behavior, MAP01 game/model/GUI/input, telemetry, or recovery efficacy is tested. The existing live-04 push remains a scoped `PASS_MEASUREMENT_INTEGRATION`; its historical output is not modified. The synthetic row does not establish that a second run has occurred.

## Frozen source

- Main commit: `2b899413d30fcee0ce97e7c69d83f7b2f69e89dd`.
- Workflow: `.github/workflows/map01-measurement-integration-live-04.yml`.
- Owner helper: `research/orchestration/o3-g7/global-owner/formal_allocation_global_owner_v1.py`.
- Actual retained push run: `34971205791` (`event=push`, `head_branch=main`, workflow path above).
- Concurrent adjacent work check: open PR #5948 tests duplicate-row pagination completeness in a separate additive path. It does not edit this workflow or path and tests a distinct input-visibility dimension; this T0 varies only the event query partition.
- Synthetic dispatch row: run ID `90000000001`, run number `2`, `event=workflow_dispatch`, `head_branch=main`, a distinct head SHA, and the same workflow path and allocation ID. This is a constructed negative control, not a GitHub run.

## Safety and repair boundary

The experiment is offline, deterministic Python with no network or external effects. Docker Desktop's UI reports the engine running, but the CLI is unresponsive and reports do not establish an exclusive resource assignment; OrbStack also has an owner-unknown nonterminal container. No engine, container, or GPU is touched. A repair belongs in a separately versioned workflow/allocation; this study does not edit live-04.
