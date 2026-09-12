# A2 revision 2 — exact tile transport with actual assistant use

2026-09-13 JST. **PASS for scoped lossless transport research; HOLD for a local
speedup, image-token saving or production-runtime claim.** This work also adds a
Python interface that the parent assistant actually used to inspect reconstructed
screenshots and operate Calc, Inkscape and XTerm.

## Fresh result

Frozen revision2 completed two fresh replicates: seeds770101–770104 and
780101–780104, four real apps, eight O1/O2 pairs/app, 64 episodes total. O1 and
O2 each achieved **32/32 success**. All **553 sampled frames** reconstructed
exactly. The independent analysis reloaded every wire packet and raw PNG,
checked image digests, metadata continuity, schedule, goals, planned input counts
and saved outputs. No pixel, sequence or final-output error was found.

| Metric | Result | Interpretation |
|---|---:|---|
| Same-trace serialized bytes | 27,196,170 → 7,961,100 | **70.73% reduction**, 95% whole-pair bootstrap CI **64.72–75.19%** |
| Live serialized bytes | 13,562,871 → 3,853,968 | **71.58% reduction**, CI **66.44–75.56%**; trajectories can have different sample counts |
| Paired task-wall difference, O2−O1 | median **+2.00 ms** | CI **−4.00 to +12.27 ms**; local speedup is not established |
| Scripted model calls | 0 | No model-token, provider-cost or model-reasoning latency claim |

The same-trace calculation re-encodes both live trajectories in every pair under
both strategies, with identical metadata/stream identifiers and a reset at each
episode. The live calculation sums the actual packets sent on each arm. They
answer different questions and must not be merged. Confidence intervals use
10,000 resamples of whole pairs, RNG65537, not correlated frames.

| App | Success O1 / O2 | Live O1 bytes | Live O2 bytes | Live byte reduction |
|---|---|---:|---:|---:|
| XTerm | 8/8 / 8/8 | 493,704 | 194,099 | 60.69% |
| Chrome for Testing | 8/8 / 8/8 | 3,191,888 | 1,330,621 | 58.31% |
| LibreOffice Calc | 8/8 / 8/8 | 2,801,736 | 979,666 | 65.03% |
| Inkscape | 8/8 / 8/8 | 7,075,543 | 1,349,582 | 80.93% |

Per-app percentages are descriptive at this small sample size. These numbers
cannot be multiplied by the earlier A1 image-reduction percentage: A2 uses a
serialized/compressed channel and a different shared Inkscape input policy.

## What changed and what it costs

O1 serializes a full frame or an exact-repeat reference. O2 additionally splits
the frame into64×64 tiles and transmits all changed tiles, including edge tiles.
Both arms use zlib level1 and the same JSON/binary envelope, with sequence, base,
action ID, capture timestamp and public context. O2 encodes full and tile
candidates and picks the smaller complete wire packet. This guarantees its
same-trace packet is no larger than this O1 representation, but charges the
additional comparison and encoding work.

The receiver reconstructs the full frame before controller/model viewing. Missing,
reordered or cross-stream bases fail without mutating receiver state. Reconnect
uses a fresh stream/full frame. Tests include geometry/mode changes, single-byte
mutations, sparse and dense changes, repeats, malformed counts and trailing
compressed bytes. Separate synthetic stress verified **2,400 decoded packets**
from1,200 frames over tile sizes1/7/16/64/128, three modes and75 paired resets,
with zero errors. This stress is functional evidence, not GUI efficacy data.

| Local per-sample metric (ms) | O1 p50 / p95 / p99 | O2 p50 / p95 / p99 |
|---|---|---|
| Encode | 5.046 / 6.283 / 7.044 | 7.183 / 10.691 / 13.592 |
| Decode | 3.501 / 4.942 / 6.034 | 1.005 / 3.011 / 4.478 |
| First action feedback | 22.601 / 80.420 / 87.661 | 22.427 / 81.937 / 94.605 |

O2 encoding is more expensive; decoding is cheaper in these observations. Pooled
component quantiles must not be added as if they were a paired total. All task
timing includes the actual codec path, while PNG/wire archival and independent
audits occur afterward. Full-screen capture still occurs. There is no simulated
network delay and no assertion that wire reduction already improves remote speed.

## A failed freeze changed the experiment

Revision1 development passed16/16, but its first fresh replicate stopped on the
31st attempted episode: Inkscape750103 O1. Visible selection handles and the
inherited30ms press dwell did not produce a moved object. All157 frames of the
failed episode reconstructed exactly; the independent SVG still had x=50.
The entire revision1 fresh efficacy comparison was rejected. The failure, raw
images, saved SVG, frozen sources and STOPPED record are retained.

Revision2 keeps the A1 frozen source untouched and adds a shared Inkscape
segmented gesture. It observes with the mouse button held and after each motion
segment, records event issue/ack times, releases the button in a finally block,
and still requires visible movement. Both arms use the same planned events;
there are no retries. The old failed seed passed both regression arms, followed
by16/16 new development episodes, a new freeze and the64 fresh episodes above.

This is observation during a planned gesture, not adaptive path correction.
It deliberately adds observation work. Its independent causal contribution to
reliability has not been isolated from scheduling/pacing changes. Root cause of
the original missed drag remains uncertain, and64 successful episodes do not
establish a rare-failure bound or universal motor correctness.

For a gesture, first feedback can arrive while the button is still held, before
the final input acknowledgment. Individual event acknowledgment and complete
gesture injection are distinct. Neither first feedback nor input acknowledgment
proves semantic completion. Image and X11 context have separate timestamps.

## Actual use → improvement → use again

The assistant used `dogfood.py` directly through stdin JSON and chose actions by
opening its reconstructed images. The benchmark task controller was not used.

- Calc: entered158/389, handled the XLSX format dialog and saved correctly.
  An unchanged image immediately after typing exposed the need for a bounded
  change wait instead of treating injection as application consumption.
- Inkscape: used the new wait, inspected selection handles, dragged and saved.
  The saved SVG preserved y/width/height and moved x from50 to77.118645.
- XTerm: used the later PNG-reference path. A deliberately unsupported `abc!`
  text command was rejected before any input, the next image remained exactly
  unchanged and reused the existing PNG. Then the assistant entered/submitted
  `t790201`; the saved output was exact.

All18 interactive observations were independently decoded again and compared
with the referenced PNGs; all three saved outputs passed. The one unchanged
reuse sample archived in5.33ms, versus31.33–43.16ms for the three newly saved
images in that session. This verifies the path and suggests a cost to measure;
one reference sample is not a randomized latency result. Full-frame PNG viewing
and outer tool scheduling still dominate parts of this exploratory adapter.
The streaming stdout messages do not establish that an LLM runtime can resume
reasoning immediately when the first local acknowledgment is emitted.

The interface remains limited to these fixture sessions and the inherited small
ASCII input set. Unsupported text is rejected atomically rather than partially
typed. Universal Unicode/IME, arbitrary app attachment, click/scroll/focus
primitives, long sessions and a model-facing adapter remain development work.

## Research and delegation decisions

[OSWorld](https://arxiv.org/abs/2404.07972) supports explicit setup and independent
execution-based scoring. [AsyncTool](https://arxiv.org/abs/2605.27995) motivates
tracking delayed feedback and dependencies, but its latency environment is
simulated. [WeaveBench](https://arxiv.org/abs/2606.09426) motivates later mixed
GUI/CLI tasks and trajectory-aware evidence; its judging does not establish
lossless delta correctness. Details and adopt/hold decisions are in
[RELATED_WORK.md](RELATED_WORK.md).

A bounded Luna subagent performed sourcing and independent reviews. Two initial
codec findings led to fixes and tests. One subsequent review reused stale source
and was corrected by requiring fresh line/hash verification; an unsupported
elapsed-time estimate was removed. This provides evidence of usefulness and
review overhead, not a controlled ranking of models or a cost/latency comparison.

## Decision and next constraints

Admit this codec as a Python research option when serialized transfer volume
matters. Retain O1 as the baseline. Do not declare O2 universally faster or
production-ready. The next useful experiments should isolate (1) PNG/reference
adapter overhead with the same agent and tasks, (2) adaptive motor feedback from
mere extra pacing, and (3) mixed-app/long-horizon behavior with focus/modal drift.
Any ROI or model-facing tile experiment must preserve the full-base recovery
contract and independently measure model task quality and actual image tokens.

Primary artifacts:

- [Protocol](PROTOCOL.md), [development/failures](DEVELOPMENT.md), [usage](README.md).
- [Fresh summary](results/a2r2-summary/summary.json).
- [Frozen r2 source/environment](results/frozen-a2r2/freeze.json).
- [Retained failed r1](results/fresh-a2r1-r1/STOPPED.json).
- [Workspace/dogfood re-verification](results/a2r2-summary/workspace-verification.json).
- [Synthetic stress result](results/stress-transport.json).

A1's six frozen hashes and A2's twelve frozen hashes were checked unchanged after
the experiments. Repository publication includes the research evidence; it does
not constitute a runnable release or production deployment. See the
[cross-chat handoff](../../docs/LOCAL_RESEARCH_HANDOFF.md) for publication context.
