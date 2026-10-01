# Capture-hold cost micro-test v1/v2

Status: **REJECT_CAPTURE_AS_PRIMARY_SIMPLE_FIXTURE_EXPLANATION** in the rendered Xvfb/Tk/XTEST fixture.

This is a deliberately small discovery loop under Issue #88. It isolates one variable: whether same-thread full-frame capture *during* a scheduled 250 ms key hold materially lengthens application-observed key occupancy.

## First outcome discipline

- v1 preregistered 20 matched pairs and was terminated by the outer execution budget before result emission. It is retained as `INCOMPLETE_OUTER_TIMEOUT`; the same task ID was not rerun.
- v2 changes only evidence retention (append+fsync each case) and reduces the pair count to 8 to fit the execution budget. Scientific conditions and decision thresholds are unchanged.

## Fixture

- CPython 3.13.5
- Linux 6.18.44 x86_64
- CPU: AMD EPYC 9V74 80-Core Processor
- Xvfb 1024x768x24 + Openbox
- rendered 900x600 Tk checkerboard
- XTEST `w` KeyPress/KeyRelease
- target hold: 250 ms
- capture arm: Pillow full-frame ImageGrab at nominal 50/100/150/200 ms
- balanced alternating order within each matched pair
- no model, ViZDoom, gameplay state, planner, renewal or shared runtime

## Result

| Metric | No capture | Capture |
|---|---:|---:|
| n | 8 | 8 |
| application-observed hold median | 250.129881 ms | 250.124353 ms |
| application-observed hold p95 | 250.226643 ms | 251.064466 ms |
| controller send-hold median | 250.123358 ms | 250.124779 ms |
| send-up -> app release median | 0.572210 ms | 0.551246 ms |
| capture work total median | 0 | 12.727938 ms |

Paired capture-minus-none application hold:

- median: **0.100535 ms**
- p95: **0.904893 ms**
- range: **-0.117994 to 1.162928 ms**

The preregistered candidate gate was median >= 5 ms or p95 >= 10 ms. Neither gate is close.

## Decision

Reject the hypothesis that the mere presence of full-frame capture work during a scheduled hold is the primary explanation for the tens-of-milliseconds physical-retention overshoot seen in more complex capture-coupled paths. The captures consumed a median 12.728 ms total but did not materially extend the application-observed hold.

This does **not** show that capture can never delay release. The next single-variable test moves capture to the release boundary: `release -> capture` versus `capture -> release`, with the same 250 ms target and authority semantics.

## Provenance

The experiment was executed before publication in the disposable container.

- immutable experimental base: `fc38624476aa1f30c381e5932f383224451a7d63`
- publication branch base: `478cde3621733bd601152dcec4c2079f6f7fda79` after a parallel agent advanced `main`
- v2 source SHA-256: `9efaad5de6ee0dc9ce765798172be7f9ede63e6f69480c9b729621722d9bc295`
- v2 preregistration SHA-256: `9e0589576822f98380bc26c7892b3cada476b09a187c34b3e6ebc5b125cbd2eb`
- v2 result SHA-256: `9a7fd8319a4f2e506ac6fedb9f0de8033b6deab8517650f054d76f5f058eb671`
- retained raw case count in the executing container: 16

The raw per-case JSONL is container evidence rather than a GitHub formal allocation artifact; the compact result, source, preregistrations, timeout record and decision are retained here.

## Scope

Development mechanics only. No ViZDoom/gameplay efficacy, human timing, hard-real-time, model, planner, or production-runtime claim.
