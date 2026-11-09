# Runtime-tracked delayed Xvfb input: R01–R07

Date: 2026-11-10. This packet investigates whether a delayed KeyPress issued through the public MCP caller can survive cancellation, whether tracked release neutralizes it, and whether the effect can reach a fresh task.

## Setup and source identity

- Worktree HEAD before these changes: `24f710366e`; branch `research/xvfb-autorepeat-release-frontier-20261110`, eight commits ahead of the then-fetched `origin/main`.
- Experimental source: `runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py`. R01–R04 used source SHA-256 `85eff51e95895284784daa49b06b33257b562b9b9d63210cd93ec9197bdc9716` and diff SHA-256 `dd0738f0614883327ecf8cf83f5578c520800e179cf08963d19a8716b642b6a6`. R05 used source SHA `c96252d447a2fd0a403386005be6cf7af3f1b024e910b3155d7b2484ecfecd2d`; R06–R07 used source SHA `987215f513c285389f8550baab21ea55ed2d8c4976c35f2415e383c2bf269e47` and diff SHA `46531c1e5ca5933cbe7ece2682db488f6a5a0293f2cfeeb0e69ad13bff6a7e1b`.
- Existing cached image only: `agent-interface-xvfb-mcp:late-input-r19`, image ID `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`. Each container used `--network none`, a read-only source mount, and a separate evidence mount. No image pull, runtime/model download, provider call, or model call occurred.
- Image reports Linux under WSL2. This is a Docker/Xvfb experiment, not a WSLc validation.
- Every run has its own prospective registration, raw JSON, X-obligation trace where available, test log, Xvfb log, and observation PNG. Exact file hashes are in `MANIFEST.sha256`.

## Current repository/issue context checked for this continuation

- Remote `main` still resolves to `0ac46b03f291ec5805d4ab54b70d8e7b7bad5e99`; this experiment source is an additive research branch based on that snapshot.
- GitHub currently reports Issue #17 as closed with reason `completed` (closed 2026-10-28), while retrieved comments still say to keep it open and describe the telemetry-independence question as unresolved. This state/comment mismatch needs separate reconciliation; these Xvfb runs do not test a blocked journal/stdout/telemetry plane.
- Issue #57 remains open/reopened (updated 2026-11-04) for integrated token-efficiency evaluation. Synthetic cancellation mechanics do not satisfy its Chromium/Calc matched economics milestone.
- Issue #7924 remains open with STOP/HOLD for WSLc ownership/current-main readiness. No WSLc state or allocation was used here.

## Outcomes

| Run | Condition | Observed outcome | Interpretation |
|---|---|---|---|
| R01 | Runtime-tracked second `a`; XTEST delay 8000 ms | Runtime published `a` as held, queued its paired release, then blocked in real `Display.sync`. Cancellation retired the owner. No late `a` event or down key was observed by the 8503 ms horizon. Old-task effect count remained 1; fresh task reached its exact effect 3. Release attempt readback was neutral, but runtime cleanup/release/task receipts stayed `UNKNOWN`/unconfirmed/null; terminal was `runtime_failed` with `EOFError`. | Scoped task and neutral-keymap oracles passed. The delayed request itself did not arrive after retirement in this run. This does not disprove another schedule. |
| R02 | Fixture directly injects untracked `b`; 8000 ms | Old `a` remained held through the wait and auto-repeat raised its effect count from 1 to 3. The independent old-task oracle failed. `b` was not observed at the horizon; the cancellation receipt remained unknown. | Not a matched control for R01: its one-`a` action schedule differs from R01’s two runtime `a` chords. Its preregistration incorrectly called the task procedure the same; this correction preserves that discrepancy instead of treating R02 as causal comparison. |
| R03 | Fixture directly injects untracked `b`; 100 ms | At the first separate-client release readback, `a` was up but `b` was still down. The test failed at the intended neutral-input assertion. The cancellation snapshot had no tracked obligations and could not release `b`. | Positive control: the fixture detects a residual delayed key when its injected event arrives promptly. It does not establish public-runtime late delivery. The failure raw is retained. |
| R04 | Runtime-tracked second `a`; 100 ms | The public operation completed all four emissions after cancellation admission but before cancellation transaction completion; its execution record contained a verified release and separate-client keymap was neutral. Old-task count was 2 against the cancellation scenario’s expected 1. Cancellation remained unconfirmed/unknown; the recorder then failed because this terminal shape lacks the liveness field it expected. Fresh-task oracle passed. | Delayed runtime input completed after cancellation admission under this timing. No temporal contradiction between a retired-owner receipt and an alive snapshot was established. |
| R05 | Runtime-tracked second `a`; 250 ms | Same broad completed-after-cancel shape as R04, but the recorder stopped at an assertion expecting top-level `cleanup_status='UNKNOWN'`; terminal completion has no such top-level field. Partial raw was retained. | Recorder limitation; R06 is the separately registered full-capture run after the observer was amended. R05 is not an independent outcome sample. |
| R06 | Runtime-tracked second `a`; 250 ms, amended recorder | All four emissions completed about 260 ms after request flush, after cancellation admission, and before cancellation transaction completion. The owner-alive snapshot was also taken before cancellation completion. The old-task count was 2 (expected 1), so that task oracle failed. Execution included a verified release and separate-client keymap was neutral. Cancellation said owner retired, cleanup unknown, release unconfirmed, replay false. Fresh task effect/count was exactly 3 and its oracle passed; the old UNKNOWN fence remained unchanged. | One late old-task effect followed cancellation admission. The owner snapshot and later retirement receipt are time-consistent; they do not establish a receipt conflict. No old input contaminated the fresh task in this run. |
| R07 | Runtime-tracked second `a`; 500 ms | Owner retired before the delayed event produced an application effect. Release attempt readback was neutral, old-task effect count stayed 1, and fresh task effect/count was exactly 3. No late `a` was observed at the 1539 ms horizon. Runtime still reported cleanup `UNKNOWN`, release unconfirmed, task success null, and terminal `runtime_failed`. | Scoped task and neutral-keymap oracles passed; cancellation status remained conservatively unknown. |
| R08 | Same runtime-tracked condition as R06; prestarted supervisor; 250 ms | The operation again completed all four emissions after cancellation admission and before cancellation completion; old-task effect count was 2 and its oracle failed. The supervisor's XRes readback was `verified` but sent zero release requests because the delayed key had already gone up. The alive snapshot preceded the retirement receipt; runtime cleanup remained UNKNOWN. Fresh task passed. | The supervisor did not prevent an already-arriving old-task effect at this timing. This does not establish a contradiction between the owner snapshot and retirement receipt. |
| R09 | Same runtime-tracked condition as R07; prestarted supervisor; 500 ms | Supervisor issued one KeyRelease request, verified a neutral keymap, and both old/fresh task oracles passed; no late `a` appeared at the 1003 ms horizon. Runtime receipt still stayed UNKNOWN, release unconfirmed and replay denied. Cancellation transaction completed 342 ms after delayed-request flush versus 879 ms in standard R07; caller response was 257 ms versus 260 ms. | One sequential pair suggests lower end-to-end custody completion time with the supervisor in this condition. It does not establish a speedup; the caller response itself was similar and the sample is n=1 per arm. |

### Randomized matched repeats (R10–R17)

The preregistered schedule uses two replicates per cell and a fixed shuffled order (seed `29112026`). All runs use source commit `9c062eb380`, the same cached image, task, cancellation hold and readback procedure. Each run executes the one target Xvfb integration test exactly once; all eight returned exit 0.

| Run | Cell | Result |
|---|---|---|
| R10 | supervisor, 250 ms, rep 2 | Operation completed after cancellation admission and before cancellation completion; old effect count 2/oracle fail; supervisor readback verified with zero release requests; fresh task pass. |
| R11 | supervisor, 500 ms, rep 2 | Old/fresh tasks pass; no late `a`; one supervisor KeyRelease and verified readback; runtime remains UNKNOWN. |
| R12 | standard, 500 ms, rep 2 | Old/fresh tasks pass; no late `a`; readback verified; standard worker does not expose a comparable release-request count; runtime remains UNKNOWN. |
| R13 | standard, 250 ms, rep 2 | Operation completed after cancellation admission and before cancellation completion; old effect count 2/oracle fail; cancellation release remains unknown; fresh task pass. |
| R14 | supervisor, 500 ms, rep 1 | Same scoped outcome as R11. |
| R15 | standard, 500 ms, rep 1 | Same scoped outcome as R12. |
| R16 | standard, 250 ms, rep 1 | Same scoped outcome as R13. |
| R17 | supervisor, 250 ms, rep 1 | Same scoped outcome as R10. |

Per-cell summaries (`n=2`, in randomized interleaving):

**Timestamp-audit correction:** R04–R06, R08, R10, R13, R16 and R17 have raw terminal status `completed`. The earlier reporter mapped that status alone to `OBSERVED_XVFB_COMPLETION_RACED_CANCEL_RECEIPT_CONFLICT`; that derived label was too strong. In all eight records, `execution.ended_ns` is after `cancellation.admitted_monotonic_ns` and before `cancellation.completed_monotonic_ns`, and the owner-alive snapshot is also before cancellation completion. The later owner-retired receipt therefore does not contradict that earlier snapshot. Raw records remain unchanged; this timestamp audit supersedes only the derived conflict label.

| Delay | Path | Old task | Fresh task | Cancel response median (range) | Transaction completion from request flush (median, range) |
|---:|---|---|---|---:|---:|
| 250 ms | Standard | 2/2 late effects; 2/2 fail | 2/2 pass | 261.65 ms (256.93–266.37) | 351.07 ms (323.87–378.28) |
| 250 ms | Supervisor | 2/2 late effects; 2/2 fail | 2/2 pass | 258.91 ms (258.38–259.43) | 352.20 ms (351.18–353.22) |
| 500 ms | Standard | 2/2 exact effect; 2/2 pass | 2/2 pass | 256.93 ms (255.83–258.03) | 754.79 ms (725.56–784.01) |
| 500 ms | Supervisor | 2/2 exact effect; 2/2 pass | 2/2 pass | 258.21 ms (257.90–258.52) | 346.40 ms (344.25–348.56) |

At 250 ms, the supervisor did not prevent completion after cancellation admission or the extra effect, and its verified empty-state readback did not resolve the cancellation receipt. In every completed 250 ms case, action completion and the owner-alive snapshot preceded cancellation transaction completion, so there was no observed temporal conflict with the later owner-retired receipt. At 500 ms, both paths passed the independent synthetic task/keymap oracles while remaining runtime-UNKNOWN. The observed transaction-completion distributions favor the supervisor in these two 500 ms pairs, but caller-response medians are effectively similar and `n=2` cannot establish a reliable latency benefit. No release-confirmed receipt was produced in any repeated cell.

R01, R02, R06–R09 each ran all six module tests successfully. R10–R17 each ran the targeted Xvfb integration test once successfully. R03 intentionally retained the positive-control assertion failure. R04 and R05 retained recorder assertion failures; R06 added terminal timing/liveness fields. A subsequent raw-timestamp audit corrects R06's earlier receipt-conflict classification: its alive snapshot precedes cancellation completion.

## What this narrows

Across the initial single-run timing points, a tracked delayed second `a` completed and added a second old-task effect at 100 and 250 ms, while at 500 and 8000 ms the owner retired before that effect was observed. The observed transition lies between the tested 250 and 500 ms points on this host/image/schedule; this is not a calibrated deadline or a reliability estimate. The 100 ms direct-injection positive control separately shows that an untracked `b` can remain down at cleanup readback.

The strongest unresolved issue is the 100–250 ms completion race: the caller accepted a cancellation request, but a delayed tracked action could finish after cancellation admission and before its transaction completed. The same occurred in both R10/R17 supervisor and R13/R16 standard repeats. At 250 ms the supervisor's verified empty-state readback did not erase the extra task effect. At 500 ms both paths preserved task effects and neutral state; supervisor transaction completion was faster in two matched pairs, but the cancellation receipt still remained UNKNOWN. Product policy should keep replay denied and not promote UNKNOWN to confirmed based on these observations.

## Limits and next experiment

All effects were synthetic Xvfb window effects. XTEST's injected delay is not a real socket/network delay, application-native behavior, WSLc experiment, MAP01 task, or model-mediated task. R01–R09 were sequential single attempts; R10–R17 were run in a randomized interleaving with two repetitions per cell. The sample remains small and host-specific. No speed, token, provider, or general task-success claim is supported.

Next, increase the matched standard/supervisor repetitions without changing the task or outcomes, then make cancellation admission semantics explicit: whether already-admitted input may finish, which receipt owns release truth, and what keeps a fresh attempt fenced. Then add a real server/socket delivery boundary before changing the horizon rule. Keep this packet and all failures intact.
