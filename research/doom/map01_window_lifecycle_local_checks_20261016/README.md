# Selected MAP01/V12 window-continuity integration

Base `4be25a072c352fde2b168cc106b7fbd84621c461`; tested code
`1af880ff8d5897eaabddc96e5379605828da091a`. Local Fake X construction only,
no formal/live allocation. `RESULT.json`, raw logs and source pins retain the
initial failures and final qualification. Initial uncommitted construction
revisions are repair history, not a preregistered scientific experiment.

## Change and discriminating evidence

The V39 controller can select `--measurement-session --target-process-identity
--target-window-lifecycle`. V15 forwards a partial of the existing process backend
with lifecycle enabled, strips its private flags before V12 parsing, and records
the selected policy with source hashes. Default V12/process-only paths do not
silently gain a window guarantee.

A backend-owned, dedicated `IdentityReader` supplies one canonical observer epoch
to both capture and the V12 input owner. Comparing tokens from independently
created observers would always mismatch; they are deliberately not compared.
Input/focus/process connections remain separate. The owner borrows the lifecycle
reader; the backend closes it, and no replacement observer is opened implicitly.

Both capture binding samples must agree before publishing process/window source
records. A complete observation binds sequence/surface/token/original deadline to
the lease once. V12 checks that source before presses and periodically while held,
and fences source mutation after its final focus query. `input_admission` and
`owner_release` records carry window context. Release does not call the lifecycle reader.

The first implementation allowed competing reads to hit the single worker slot,
and retained a healthy-case refusal. The repaired window slot polls each caller's
original deadline/cancel while serializing reads. No unbounded lock wait or second
monitor fallback is added. A capture can still exhaust its local query budget,
retire the canonical monitor and invalidate the active intent. This trades
availability for refusal; fairness, native availability and cost remain unqualified.

Seven new composition methods exercise the actual capture/backend/Executor/V4/V12
path with the real lifecycle reader and Fake X transport: healthy capture/lease/
admission/release, same-process same-XID stale rejection, destruction during
capture, final-source mutation, held-query cancellation/expiry before gate resume,
and overlapping capture without a second monitor or release wait. Two selection
methods additionally cover prerequisites, forwarding, stripping and policy pins.

Final affected entry: **58 isolated modules, 427 methods, 12 explicit skips, zero
failed modules**, in both normal and optimized Python. The skips include optional
real-Codex and platform-only controls. See per-module logs and summaries. These
are ordinary regression checks, not repeated formal allocations or physical timing
measurements. The first RED and collision failures remain, without changed verdicts.

```text
python -B research/doom/check_map01_control_regressions.py --output-dir /absolute/fresh/normal
python -B research/doom/check_map01_control_regressions.py --optimized --output-dir /absolute/fresh/optimized
```

The saved A03 candidate fixture must be materialized from Git in a sparse checkout,
as documented by the work map; never regenerate it with its historical producer.

## Limits and next boundary

This does not run Doom, a native display/input route, model/provider or WSLc/container
allocation. There is no new task effect, bounded task recovery or matched economics
result. Direct-window semantics still assume a trusted X server, reliable ordered
connection and honest events; arbitrary undetected loss and final check/use races
remain. Native input send/readback stalls are not interrupted or qualified.

The shared monitor is a per-backend mechanism, not global process/device custody.
Cross-backend authority remains a separate unresolved boundary. Next qualify
native subscription/coverage and source-to-owner timing with an authorized fresh
allocation, preserving independent effect/recovery predicates and all attempts.
No old #3950/#4039 allocation or saved MAP01 producer was rerun here. #5/#17/#59/#57
remain open in their unproved scopes.
