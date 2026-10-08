# Mindustry positive/no-match/unreadable live block v1

## Fixed comparison

One preregistered ordered block used the same Linux/X11 fixture, Luna-low model,
palette path, schema set, input authority and independent scorer in three fresh
private GUI sessions. The schema gate passed from hash-pinned cache before the
first application process; it made zero fresh endpoint calls.

The conditions were fixed as:

- `positive`: the original directly-above target with normal verified world
  receipt pixels;
- `no-match`: a tile thirty tiles north of the source, outside the fixed current
  viewport, with panning and substitution forbidden;
- `unreadable`: the original target and live verified hover, with only the
  planner presentation pixels replaced by their deterministic mean.

No condition or model call was retried.

## Results

| Condition | Typed result | Placement button | Independent task | Calls | Input tokens | Decision to evaluation |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| positive | `EVIDENCE_BOUND` | 1 | verified | 4 | 35,017 | 51.761s |
| no-match | `NEEDS_DECISION: ambiguous` | 0 | contradicted as expected for abstention | 3 | 26,689 | 31.239s |
| unreadable | `NEEDS_DECISION: unreadable_evidence` | 0 | contradicted as expected for abstention | 4 | 35,025 | 42.144s |

The positive session admits `select-conveyor` and `place-one-conveyor`, then the
engine verifies the exact north-facing tile, copper -1, unchanged 111 other
guard tiles, preserved source/core and paused idle completion. The negative
sessions admit only `select-conveyor`; no world placement button is issued,
copper remains unchanged and the 112-tile guard remains clean.

Across 11 calls, reported usage is 96,731 input tokens, including 16,640 cached
input tokens, plus 1,766 output and 1,138 reasoning-output tokens. The sessions
use 14/6/8 socket exchanges and 33/14/23 exact frames. Runtime world-hover reply
is 1.985s in positive and 2.053s in unreadable. Sequential whole-session times
are descriptive and do not establish a speedup.

## Formal failure and retained evidence

The preregistered block is **false** overall. The no-match condition stopped at
the correct boundary with no coordinates, world hover or placement, but Luna
classified the reason as `ambiguous`; the preregistered gate required
`no_candidate` or `no_match`. The interface preserved safety while the reason
taxonomy lacked the requested precision. The run was not retried or relabelled.

The unreadable fault is deterministic and explicit. It proves that the typed
receipt branch can suppress placement after live evidence becomes unavailable;
it is not evidence of a natural error rate. Likewise, this three-case block is
not a broad reliability, token-saving or human-tempo result.

Windows and WSL audits reconstruct all 70 exact frames, 11 raw model turns,
28 socket exchanges, 11 released input programs, three independent engine
scores and both presentation variants. Decision:
`RETAIN_PARTIAL_BRANCH_EVIDENCE`.

Primary artifacts:

- `results/mindustry-single-tile-matched-01/preregistration.json`
- `results/mindustry-single-tile-matched-01/report.json`
- `results/mindustry-single-tile-matched-01/audit.json`
- `run_mindustry_single_tile_matched_v1.py`
- `audit_mindustry_single_tile_matched_v1.py`

The next candidate should collapse negative reasons to an operational class
when they grant identical authority, or measure reason precision separately
from the hard no-coordinate/no-placement safety gate. It should not repeat this
fixed block merely to obtain the preferred label.
