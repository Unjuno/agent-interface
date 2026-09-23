# OpenTTD road-placement oracle calibration — 2026-09-13

Follow-up: [visible saved task and read-only observer](../openttd_task/README.md)
now provide the initial fixture and two fresh save-load checks.

The independent scorer now distinguishes **empty, partial, complete and extra
placement** on two real OpenTTD 13.4 worlds. This removes one prerequisite for
a small dense-GUI placement pilot. It is not assistant gameplay, shared-runtime
validation, benchmark adoption, or a freeze-qualifying revision.

## Contract and result

Before execution, `plan.json` declared seeds 991001/991002, the first row-major
flat/buildable 3x2 rectangle, and expected stage outcomes. The upper three tiles
are targets; the lower three form a forbidden region. A success requires:

- Roads on all target tiles, owned by company 0.
- Both adjacent pairs connected in both directions.
- No road in the declared forbidden row.

The contract is fixed from the initial setup observation, not rediscovered from
each submitted state. The Python scorer receives tile/connection observations;
it does not trust a success flag from the fixture builder.

| Actual engine state | Seed 991001 | Seed 991002 | Reason |
|---|---|---|---|
| Empty | reject | reject | targets and connections missing |
| First road link only | reject | reject | final target/link missing |
| Both required links | accept | accept | ownership, connection and forbidden-region checks pass |
| Required road plus road on adjacent forbidden row | reject | reject | forbidden placement present |

The final row is an actual engine-generated counterexample to **target count
alone** as a complete placement scorer: target ownership and connectivity still
pass while the task is incorrect. The earlier feasibility count was only a
negative smoke probe; it was never a qualified scorer for this new contract.

Separate counterfactual checks change the required owner, remove a connection
from the observation, or omit a tile. All are rejected. These three checks are
synthetic scoring controls over real snapshots, not additional gameplay trials
or proof of an actually constructed wrong-owner/one-way road scenario.

## Scope and separation

GameScript builds the calibration fixtures using engine APIs and exports state
through logs. **There is no agent in this experiment.** The future UI pilot must
use a setup-only builder and a read-only observer after the control boundary;
do not ship this mutating calibration script as the agent's action interface.

Eight engine observations come from two sequential four-stage runs, not eight
independent episodes. Targets differ between seeds: 678–680 / 742–744 for the
first map, and 465–467 / 529–531 for the second. The oracle only checks six
declared tiles and two bidirectional edges. It does not prove absence of damage
elsewhere, route usefulness, cargo delivery, timing, screenshot freshness or
long-horizon planning. Save/load reset and shared pointer/button/drag/wheel
semantics remain open. No speed or token claim follows from this study.

## Preserved development failures

- Cohort 01, two attempts: the script used an unavailable global `format`
  function and died before emitting the initial snapshot. The original runner
  then reached its bounded observation timeout before cleaning up the app.
- Cohort 02, two attempts: string serialization worked, but the first engine
  build returned false. The original failure record did not include an engine
  reason; do not retroactively assign one.
- Cohort 03, two attempts: an attempted company-readiness guard called an
  unavailable `GSCompany.IsValidCompany` method.
- Cohort 04, two attempts: the 13.4-supported `ResolveCompanyID` readiness guard
  plus a 30-tick setup wait preceded construction. Both seeds reached all four
  stages. This does not isolate which startup condition caused cohort 02.

Every cohort has a source manifest, raw stdout/stderr, a final source screenshot
and cleanup record. The original and corrected sources remain separate.
Some failed cohort runners overlapped while awaiting their bounded cleanup;
there is no timing comparison between these runs. All eight owned process
groups exited. The final screenshot records application state, not a visual
assertion that the offscreen target road was inspected by an assistant.

## Reproduce and audit

Use the pinned user-local assets from
`research/benchmark_discovery/REPRODUCE.md`. From the repository root in Linux:

```sh
python3 research/openttd_oracle/run_v4.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out /home/taka/openttd-oracle-rerun
python3 research/openttd_oracle/score.py /home/taka/openttd-oracle-rerun
```

For the committed evidence:

```sh
python research/openttd_oracle/score.py research/openttd_oracle/results/cohort-04
```

`results/cohort-04/audit.json` contains each contract, component check and
expected outcome. The evaluator verifies the recorded source hashes and exact
stage sequence before grading. Its parser/scorer is research code for the
declared schema, not a hardened general-purpose untrusted observation service.

Next: split out a non-mutating observer and freeze a reusable task/save with a
visible target. Verify restore and reset, then connect the shared pointer
semantics and conduct actual assistant use. Preserve existing keyboard/DOOM
correctness while adding this coverage axis.

API behavior was checked against the
[OpenTTD 13.4 road API source](https://github.com/OpenTTD/OpenTTD/blob/13.4/src/script/api/script_road.hpp)
and [company API source](https://github.com/OpenTTD/OpenTTD/blob/13.4/src/script/api/script_company.hpp).
The [current GSRoad documentation](https://docs.openttd.org/gs-api/classGSRoad)
also explains that adjacency alone does not imply a traversable connection;
the executable evidence here uses pinned 13.4, not the current documentation build.
