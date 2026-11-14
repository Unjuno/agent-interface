# MAP01 Win32 expiry-caller comparison — prospective freeze

Status: **protocol draft; not an experiment freeze**. No allocation or live attempt started. This is a candidate protocol for PR #10304, not evidence and not an authorization to use an unknown allocation. The host currently has no `gzdoom.exe` on PATH and no running `gzdoom` process. Exact action bytes, runtime/asset hashes, caller scheduling implementation, oracle calibration, and allocation identity must be attached and reviewed before calling a run frozen.

## Question and estimand

For the same current-main supervised Win32 MAP01 dispatch, does routing lease-expiry cancellation through one exact-call public `interface_cancel` request change elapsed time or local resource use relative to the existing automatic deadline monitor, while preserving the same release, no-late-input, two-horizon, effect, and close outcomes?

Compare only expiry-trigger routing. Producer, action sequence, MAP01 state, lease, effect oracle, owner recovery, grace, machine, runtime build, and input timing remain fixed. This estimates a local mechanism interval, not model-mediated agent efficiency, population reliability, or general GUI performance.

## Arms and immutable conditions

- **A — automatic:** server policy `automatic`, unchanged production default; no public cancellation request is sent.
- **B — public caller:** candidate server policy `public_caller`; exactly one dedicated local caller waits until the authority's `expires_at_ns`, then sends `interface_cancel(call_id)`. Configure a 250 ms bounded grace. Any caller request rejected as early, missing the grace, duplicated, or arriving after monitor fallback invalidates that arm; retain it as a failure and do not retry.
- Run each arm from a separately launched, verified baseline with HUD ammo exactly 50 and the same pinned MAP01 asset/runtime state; mint unique program, lease, attempt, and call IDs every time. Freeze one exact action program whose pre-expiry attack produces the calibrated HUD ammo transition 50→49, with an independently specified post-expiry delayed action that must remain excluded. The initial attack's DOWN dwell, transition spacing, wait, and exact delayed operation must be captured in the signed condition file before either arm. Do not copy IDs or reuse a previously executed R187–R197 condition packet.
- Require the public caller and MCP server to run on the same Windows host and use the same verified monotonic clock domain. If this cannot be established from the caller/server environment, do not run B; remote-clock scheduling is not an equivalent arm.
- The B caller must retain the exact `authority.expires_at_ns` it put in the dispatch request and bind it to the exact `call_id` returned by the immediate `wait_for_result_ms=0` pending dispatch response. Once the owner has admitted the action, `interface_results(call_id)` returns the owner result and does not expose the original dispatch arguments/deadline; do not use it as the deadline source. Schedule one asynchronous exact-call cancel at the retained absolute deadline while dispatch remains in progress. An in-process MCP harness now verifies this API shape and recovery join. A separate no-input stdio/client timing check is still required before target use. If the actual transport/client cannot return the pending `call_id` before the lease expires or cannot schedule within grace on the same host clock, the arm is infeasible and the study must be redesigned rather than approximated.
- Use the same 250 ms configured grace in B for the bounded fallback. A's policy has no handoff grace, so grace waiting is part of B's treatment and must be included in the latency endpoint.

## Schedule and denominator

Run four counterbalanced pairs, eight attempts total: **A-B, B-A, B-A, A-B**. Freeze the schedule and condition hash before the first target launch. Each attempt receives a unique ID and a full preflight/postflight custody snapshot. All eight attempts remain in the denominator, including setup, transport, caller-scheduling, recovery, oracle, and close failures. Stop the block on custody ambiguity, unexpected input, process-identity change, or any incomplete release; retain partial raw evidence and declare no speed winner.

## Required per-attempt timestamps and records

Retain monotonic timestamps for client dispatch submission, server call registration, authority expiry, caller cancel submission/acceptance (B only), recovery entry, release acceptance, owner-bound neutral horizon completion, independent neutral horizon completion, calibrated effect observation, target close request, and observed process exit. Also retain exact program and lease, operation/generation/source-action identifiers, owner and release receipts, queued/delayed input disposition, HUD raw image plus independent classification, target PID/HWND, process exit code, CPU time, peak working set, full request/result/exception logs, and packet manifest with hashes.

Primary timing endpoints are (1) dispatch submission to verified release plus both horizons and calibrated effect, and (2) dispatch submission to observed normal target exit. Report each trial and paired differences; report median and range descriptively. Record CPU/peak working set over each full lifecycle. Provider/model calls are deliberately absent in this infrastructure-only pair; report token and provider cost as **not applicable / zero calls observed**, never infer agent-model savings from it.

## Pass gates and interpretation

Each arm must independently show: exactly one pre-expiry attack accepted; exact HUD 50→49; no delayed post-expiry operation accepted; producer terminal state and source-action uncertainty preserved as specified; distinct LEFT and modifier release confirmations; bounded recovery; owner-bound and independent continuous-neutral horizons both complete; custody clear; target closes normally without forced termination; and all raw artifacts hash-verified. If any arm fails a gate, publish the full attempt denominator and descriptive observations only—no efficiency winner. A successful 4-pair block is still a small scoped experiment and does not close #57 without the issue's broader matched accounting requirements.

## Preflight blockers

Before allocating: verify the pinned current source commit and asset hashes, live target installation and launch route, current custody clear, exclusive fresh allocation identity, same-host clock-domain proof, caller scheduling implementation, oracle calibration, and local collector space. The live target prerequisite presently fails. No Docker action, runtime download, installation, launch, input, or allocation claim is part of this freeze.

