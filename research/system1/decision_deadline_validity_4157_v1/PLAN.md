# Issue #4157 — explicit decision deadline validity v1

## Goal
Test whether proposal lateness can be semantically invalid even when observation identity, epoch, freshness and lease remain valid.

## H
`EXPLICIT_DECISION_DEADLINE` rejects proposals whose actual `proposal_ready_ns` is later than an externally authored deadline, while preserving required on-time proposals. `EXISTING_CURRENTNESS_ONLY` should expose at least one admitted action whose independently observed application receipt is semantically late.

## T
- Linux x86_64 execution container, CPython standard library only; no network/model/GUI/input.
- Separate cooperative application process publishes a static observation plus an absolute monotonic decision deadline 120 ms later. Its displayed state never changes.
- Existing freshness and lease remain 400 ms, so every primary proposal remains nominally current by those contracts.
- Proposal target delays after observation: 20, 90, 150, 260 ms.
- Two policies × four delays × three repetitions = **24 fresh cases** (`n_min=24`).
- One source-frozen invocation. No case retry, replacement, exclusion or post-result gate tuning.
- A separate policy process receives the same packet in both arms except policy name. A prestarted application process records actual action-receive time and semantic validity against the same authored deadline.

## D
`PASS_DEADLINE_VALIDITY_SCOPED` iff:
1. all 24 cases and required process receipts are present;
2. both policies admit all 20/90 ms proposals and application receive time remains on-time;
3. currentness-only admits every 150/260 ms proposal and those resulting effects are independently late;
4. explicit-deadline refuses every 150/260 ms proposal with zero effect;
5. every primary proposal is still within the frozen lease and freshness budgets;
6. authority remains false; audit has zero errors; >=8 copied-evidence mutations reject after intact-copy validation.

`FAIL_DEADLINE_REDUNDANT` if ordinary currentness already rejects all late primary proposals. `FAIL_DEADLINE_REJECTS_VALID` if deadline policy rejects an on-time proposal. Infrastructure/provenance ambiguity is `STOP_INFRASTRUCTURE_OR_PROVENANCE`.

## C
Competing explanations: ordinary lease/freshness may already suffice; proposal-ready time may be the wrong endpoint; application dispatch may cross the deadline after an on-time proposal; task-specific deadlines may not generalize.

## U
No universal latency target, OS action, model quality, token saving, production authority, clock translation or hard real-time claim. Same `CLOCK_MONOTONIC` domain only. Directed repetitions are finite coverage, not failure-rate estimates.

## Variable table

| Symbol / field | Meaning | SI unit | Definition | Domain / premise | Type |
|---|---|---:|---|---|---|
| `t_obs` | observation available time | s (stored ns) | `observation_available_ns` | CLOCK_MONOTONIC | scalar integer |
| `t_ready` | proposal ready time | s (stored ns) | actual timestamp after injected delay | `t_ready >= t_obs` | scalar integer |
| `t_deadline` | decision deadline | s (stored ns) | `t_obs + 0.120 s` | fixture-authored | scalar integer |
| `t_lease` | lease validity end | s (stored ns) | `t_obs + 0.400 s` | fixed | scalar integer |
| `B_fresh` | freshness budget | s (stored ns) | `0.400 s` | fixed | scalar integer |
| `t_dispatch` | action-send time | s (stored ns) | immediately after policy ADMIT | diagnostic | scalar integer / null |
| `t_effect` | application action-receive time | s (stored ns) | app process receipt | same monotonic domain | scalar integer / null |

### Dimensional check
Every compared quantity is a monotonic timestamp in ns or a duration in ns. `t_ready - t_obs` and `B_fresh` both have dimension time; `t_ready <= t_deadline` compares two timestamps in the same clock domain.
