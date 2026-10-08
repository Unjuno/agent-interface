# Mindustry changed-geometry single-tile placement v5

## Question

Can the same Luna-low planner bind a Mindustry palette control and a separate
world target through different active visual receipts, then place exactly one
independently scored tile outside the earlier eight-tile route?

The fixed task places one north-facing Conveyor at `(137,52)`, directly above
the copper item source at `(137,51)`. The controller never receives engine tile
state. The scorer reads the bounded engine projection only after control closes.

## Development observation

A click-free world hover produced an animated placement preview. Ordinary
`pixel_quiet` settling timed out because the preview arrow changes colour, even
though its semantic location stayed fixed. The world receipt therefore requires
one pointer move, stable focus and surface binding, a bounded settle, and the
same nonzero change mask against the pre-hover frame across every dwell frame.
The formal successful receipt has seven frames and 1,972 changed pixels in each
frame. Palette tooltip receipts retain their stricter exact-pixel persistence.

A model-free GUI calibration placed the new tile and established the independent
positive: Conveyor/team1/rotation1 at the target, copper delta `-1`, no change in
the other 111 guard tiles, preserved source/core and paused live unit with zero
pending plans. Wrong rotation, collateral placement, wrong cost and a pending
plan each contradict; malformed target metadata returns unknown.

## Retained failure sequence

| Version | Retained outcome | Completed model calls | Input tokens | Button-downs | Placement button-downs |
| --- | --- | ---: | ---: | ---: | ---: |
| v1 | Existing schema was valid, but its redundant direct point was absent from its candidate array; local validator refused | 1 | 9,313 | 0 | 0 |
| v2 | Candidate schema used unsupported top-level `oneOf` | 0 | unavailable | 0 | 0 |
| v3 | Flat candidate contract passed; world-receipt schema still used unsupported `oneOf` | 3 | 26,652 | 1 | 0 |
| v4 | Flat world receipt had a constant property without the explicit `type` required by the endpoint | 3 | 26,652 | 1 | 0 |

Each version was a separately preregistered first allocation. None was retried.
Raw model/API records, all available usage, exact frames, absence of placement
input and cleanup remain preserved. Windows and WSL audits reconstruct all four.
The failures motivated [Issue #54](https://github.com/Unjuno/agent-interface/issues/54)
for an endpoint-compatible schema preflight before GUI launch.

## Contract corrections

The candidate result now has one `points` array instead of simultaneous `point`
and `points` fields. A direct result has one point, a probe has one to three,
and a bounded stop has an empty array. Palette binding additionally refuses a
coarse point more than 48 pixels from every slot in the fresh screen-derived
palette. Thus a world coordinate cannot be silently snapped into a palette cell.

The world receipt uses the same flat structured-output-compatible pattern. A
positive result contains the one printed receipt point. A negative result has an
empty point array and cannot reach the placement path. The v5 run exercises the
positive branch; recorded local controls exercise coordinate-free refusal. A
fresh negative GUI case remains required before claiming live abstention quality.

## Preregistered v5 result

- requested planner: `gpt-5.6-luna`, low reasoning;
- subagents: zero;
- palette coarse point: `[1004,580]`;
- fresh detected palette slot: `[1007,577]`, distance 4.243 pixels;
- palette receipt: exact persistent Conveyor tooltip;
- world coarse point: `[368,392]`;
- world receipt: seven animated frames with one stable preview mask;
- admitted button-downs: `select-conveyor`, then `place-one-conveyor`;
- socket exchanges: 14;
- completed terminals: 6, all with verified input release;
- exact transported frames: 33;
- bridge exit: 0.

The post-control engine scorer verifies the exact target block, team and north
rotation, copper delta `-1`, no collateral guard change, preserved source and
core, and paused idle completion. Decision: `RETAIN_SINGLE_TILE_PLACEMENT`.

## Timing and model usage

| Boundary | Result |
| --- | ---: |
| Palette hover acceptance → first tooltip frame ready | 294.158 ms |
| World hover acceptance → first preview-receipt frame ready | 457.934 ms |
| World hover submission → terminal reply | 2,008.754 ms |
| Placement acceptance → first image ready | 270.075 ms |
| Placement acceptance → released terminal | 816.507 ms |
| Decision start → world receipt ready | 36,559.207 ms |
| Decision start → semantic world binding | 46,467.482 ms |
| Fixed build wait | 3,000.104 ms |
| Decision start → independent completion | 53,462.741 ms |
| Four model runner durations, summed | 37,796.167 ms |
| Four parent-observed model durations, summed | 39,022.520 ms |

The four-call ledger reports 34,967 input tokens, of which 4,864 were reported
cached input, plus 912 output tokens and 671 reasoning-output tokens. Cached
input is a subset of input and is not added again. All calls, including the
fourth receipt decision, reconcile with their raw turn records.

The subsecond values are runtime feedback boundaries. The full task remains
dominated by four sequential planner calls and is not human-tempo performance.
No matched baseline establishes a speedup or token saving.

## Limits and next step

This is one fixed-screen changed target and one successful positive allocation.
It establishes palette/world evidence separation, animated receipt handling and
one independently scored placement. It does not establish a success rate,
negative live abstention, changed camera/window geometry, delivery, long-horizon
planning or general Mindustry control.

Next, preflight planned schemas before GUI launch, then run a finite matched
block with one positive target, one no-match target outside the allowed search
area and one ambiguous/unreadable receipt. Account for every probe, model call,
safe stop and eventual task result. Do not promote the contract from this single
positive case.
