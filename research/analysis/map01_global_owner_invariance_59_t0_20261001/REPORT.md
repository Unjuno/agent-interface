# Issue #59 — global-owner event/head invariance T0

## Result

**FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER** (synthetic source-composition counterexample; not a live duplicate-run observation).

The frozen live-04 workflow requests runs with `event=$GITHUB_EVENT_NAME&per_page=100`. The frozen production `select_global_owner` helper itself correctly denies a second run when given complete workflow-path history. When composed with the workflow's event-filtered response, however, each of four prior-owner cases from a different event is hidden and the current run receives `PASS_CANONICAL_GLOBAL_OWNER`. This holds for both equal and different head SHAs and for both event directions. The two same-event prior-owner cases are denied. A no-prior-owner control admits, and the helper fails closed on a truncated response.

| Check | Outcome |
|---|---|
| Cross-event prior owner, event filter applied | 4/4 admitted |
| Same cases, complete workflow-path history | 4/4 denied |
| Same-event prior owner | 4/4 denied |
| First-run control | admitted |
| Truncated API-view control | denied (`UNCERTAIN_TRUNCATED_API_VIEW`) |
| Independent raw-output audit | PASS, 8/8 matrix rows, zero audit errors |

### H / T / D / C / U

- **H:** The path-global allocation owner can be bypassed when the workflow-run request filters by current event, regardless of whether the hidden prior owner's head SHA matches.
- **T0:** Eight synthetic event × event × head-SHA cells, actual frozen workflow query scope, actual frozen production owner helper, two controls. No API, Actions, network, or live allocation was used.
- **D:** The preregistered failure threshold was four cross-event admissions with complete-history denial, correct same-event rejection, passing first-run control, and fail-closed truncation control. All conditions were met; the independent auditor returned `FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER` with no audit-integrity errors.
- **C:** A workflow concurrency/scheduling rule could prevent simultaneous execution but was not represented. This result does not show that two real runs overlapped or entered a formal step.
- **U:** Live Actions reachability/overlap, Docker/game/model/GPU/GUI/input, release telemetry, and MAP01 efficacy remain untested. No live run was allocated.

## Reproducibility and immutable outputs

Source commit: `ad123c3875d81ebdc8bdfbdb59340005d705a60d`.

- Workflow blob: `45279028918eff71332e627b1f783dfb11d27e49`, SHA-256 `2bd3735425378ab18a9b5e464fe38fe8ee9afc3d15ada45ce9bab1bc12970881`.
- Production helper blob: `f07f928f67a7a6c670d399efb23d67246506c802`, SHA-256 `0b1056c6cbd95288d2c1934a471d2a04b9c000cd1114da7a49310afc850b87fd`.
- Candidate output SHA-256: `6bf315d2ff750e9c4e16f9d6adacbd24a81838a06eba07d1651a8cc29778d9de`.
- Independent audit output SHA-256: `ca40940debc24a962ea9aa9ba9072238cec872701db1b9a8de12dcc50d779eae`.

`FREEZE.json` pins the protocol inputs; `AUDIT_FREEZE.json` pins the candidate bytes and auditor before adjudication. The candidate and auditor each ran exactly once. `RUN.md` records commands and `SHA256SUMS` records the full artifact manifest. Docker Desktop was unavailable; this deterministic standard-library source fixture did not require a container.

## Disposition / next step

Retain the counterexample as T0 evidence. Do not silently change this result or treat it as a live incident. The next useful test is an additive, fresh-main successor that removes the event filter (or obtains complete workflow-path history), retains the global owner helper, and exercises bounded duplicate/concurrency and pagination controls. Only after an independently reviewed fail-closed workflow change should a separately authorized fresh no-retry Actions allocation be considered. Existing #5936/#5953/#5948/#5969 evidence is not modified or retried here.
