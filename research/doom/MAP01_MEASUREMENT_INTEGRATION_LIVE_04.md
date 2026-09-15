# MAP01 measurement integration live-04

Status: **FORMAL PASS — one-shot measurement gate closed.**

Allocation: `map01-measurement-integration-live-04`  
Frozen commit: `e947b9809a3449de837e45211a4cb416d990279a`  
Workflow run: `34971205791` / run number 1 / branch `main`  
Artifact digest: `sha256:11c51e8302665c3c06f07e3c6bc8b35db9cb40b891f85f2042a3c7f439025c2f`

Live-04 exists because live-02 and live-03 each exposed a different formal-allocation duplication failure. This allocation used a new main-only versioned workflow path, non-cancelling concurrency, workflow-path-global launch ownership, exact runtime Git blob pins, zero model calls, one run and no retry.

## Result

Every predeclared hard gate passed:

- exactly one workflow run exists for the live-04 allocation at retention time;
- launch receipt is `PASS_CANONICAL_GLOBAL_OWNER`, owner run `34971205791`, matching-run count 1, branch `main`;
- all frozen runtime blob identities matched before the formal probe;
- MAP01 measurement integration audit passed;
- one normal two-key hold completed and emitted two verified direct release transitions;
- direct retained-input analyzer was measurement-ready with zero invalid releases and zero unmatched admissions;
- independent scorer remained isolated from controller events and produced 18 samples with no integration-audit failure;
- exactly one direct final scorer sample existed and exactly matched `score.json` on all five terminal fields;
- terminal release was verified empty.

Direct owner-commanded retained-input bounds for the 250 ms requested hold:

| key | lower | upper | censor width |
|---|---:|---:|---:|
| `d` | 250.477537 ms | 250.789463 ms | 0.311926 ms |
| `a` | 251.277945 ms | 251.663478 ms | 0.385533 ms |

The release batch window was 403.041 microseconds. Invalid-release count and unmatched-admission count were both zero.

Terminal scorer agreement was exact for `map_exit=false`, `episode_finished=false`, `player_dead=false`, `death_count=0`, and `kill_count=0`.

No positive useful event was expected or required in this measurement-only allocation. Therefore this result validates instrumentation and experiment launch integrity, not recovery efficacy or gameplay competence.

## H / T / D / C / U

**H — falsifiable hypothesis.** The v13 MAP01 measurement stack can provide direct bounded normal-release telemetry and isolated independent scoring in one protocol-valid formal allocation.

**T — minimum test.** One main-only, zero-model, no-retry formal run with frozen runtime blob identities, global launch ownership, one normal two-key hold, direct retained-input audit, independent scorer cadence, empty terminal release and strict final score agreement.

**D — decision.** **PASS measurement integration.** The previous instrumentation blocker is closed. This PASS authorizes construction/execution of the separately preregistered matched coast-vs-bounded-recovery experiment; it does not itself establish useful-control efficacy.

**C — break modes.** This is one short MAP01 measurement episode; planner/model overlap, natural threat variation and recovery policy utility are not exercised. The direct release interval remains bounded rather than an atomic hardware-edge timestamp. A future workflow version can still fail if its own allocation-global launch gate is altered.

**U — uncertainty.** Dominant uncertainty now moves from telemetry mechanics to transfer/efficacy: whether an explicitly bounded prior action is useful during real planner wait under changing MAP01 observations, whether independent progress events are sufficiently exposed, and whether matched terminal outcomes separate recovery from coast.

## Next gate

Implement the already-frozen `map01-recovery-cover-matched-v2-prereg` without relaxing thresholds. The formal recovery allocation must use a new main-only workflow path, the live-04 global-owner launch protocol, the same v3 release telemetry and independent scorer, and retain exactly one first outcome. Scientific PASS requires both reduced no-retained-input time and independent useful outcome evidence; continuity alone is `HOLD_MECHANISM_ONLY`.
