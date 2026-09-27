# MAP01 final-admission live v32 and schema-v6 endpoint preflight

Two previously frozen first-outcome allocations have now been executed once
each. The schema-v6 preflight made one Luna-low/no-image/no-GUI endpoint
request. The endpoint accepted the locally valid schema and returned one
schema-valid answer with complete usage:8,125 input and43 output tokens. This
proves request compatibility for that pinned CLI/runner/instructions identity;
it does not prove correct MAP01 policy or v38 live behavior.

The v32 live allocation used the retained `map01-threat-contact-v2` fixture,
Luna-low, six decision turns and continuously advancing Freedoom MAP01. Source
hashes and the one-run/no-retry stop condition remained unchanged. Exact
initial and later temporal frames visibly contain an enemy. The six-turn run
completed after59.752s of control time and57.150s of model-wall time. The
independent scorer recorded one kill, zero deaths and no map exit; the episode
was alive but unfinished. This is a bounded controller test, not a clear
attempt or success claim.

| Final-admission result | Decisions | Executed plan admissions |
|---|---:|---:|
| `REJECTED_POLICY_INVALIDATED` | 5 | 0 |
| `INPUT_ADMITTED` | 1 | 1 |

The retained runtime emitted229 exact observations. Ten programs were accepted
(nine cover programs and one primary plan), and every matching terminal
verified empty keys and buttons. Four decisions were interrupted; decision4
returned `completed`/answer eligible, but its action was still rejected.

Decision4 is the decisive race. The planner terminal was observed first.
Before controller admission, the cover-policy monitor evaluated an exact
health79 observation and found the model-authored source lease expired:
`source_age_ms=12,214.235`. The interrupt replied `already_terminal`, yet
the final receipt became `REJECTED_POLICY_INVALIDATED`/`source_expired`; no
`plan-4-*` program was accepted. This preserves the intended precedence:
planner protocol completion does not itself authorize input after an observed
policy invalidation. It is an expiry/unknown race rather than a newly damaged
health-value crossing, so it should not be counted as a natural below-floor
combat transition.

The liveness result remains weak. Decisions0,1,2,5 invalidated on
`below_hard_minimum`; decision4 invalidated on source expiry; only decision3
admitted an action. Cover-validity soft events were0. Decision3 completed
and authored the next cover. During decision4's approximately11.78s model
interval, that prior cover's source lease expired, so decision4's returned
answer was discarded before new input. The remaining four interrupted-turn
usage records are unavailable
and may contain repeated cumulative notifications; do not sum them as zero or
infer a six-turn total from the two complete receipts. The preflight usage is
separate from gameplay usage.

This first outcome isolates two next questions. First, integrate the
already-built schema-v6/v38 planner path with immediate action validity,
continuous running-action validity, typed pre-artifact health/ammo and
two-phase physical release; v38 construction tests alone do not show live
behavior. Second, under real threat exposure, measure whether local policy
renewal remains useful when its source lease is nearing expiry, and whether
the runtime can stop or switch it from new evidence before a slow model
returns. Do not extend an authored lease merely because observed health is
unchanged; a changed policy/lease rule requires a distinct versioned test.

The preflight's original endpoint audit and a new raw-retention audit pass on
Windows and WSL. File-level SHA-256 manifests bind13 preflight files/9,060
bytes and484 v32 files/65,814,543 bytes. The v32 audit checks source hashes,
temporal image hashes, decision receipt/terminal ordering, one plan acceptance
versus five zero-input rejections, all ten empty releases, exact observation
coverage and independent score. Neither audit makes a cross-allocation
latency or survival comparison. See
[`v32 prereg`](map01_final_admission_v32_live_v1_prereg.json),
[`v32 report`](results/map01-final-admission-v32-live-01/report.json) and
[`schema-v6 preflight`](results/map01-schema-v6-preflight-01/report.json).
