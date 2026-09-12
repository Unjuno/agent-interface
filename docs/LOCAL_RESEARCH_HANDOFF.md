# Local research handoff — 2026-09-13

This is the entry point for discussion in another chat. The user has authorized
direct updates to `main` when validated progress is ready. Keep successes,
failures, reproducible code and remaining limitations together in each update.

## Objective

Let the assistant itself operate a changing screen at an ordinary human-like
tempo. Optimize the full observation–decision–action loop, including unnecessary
model/tool boundaries, waiting, input/observation representation and actual token
cost. Preserve task correctness and information needed for decisions. Human-like
performance, real token savings and production readiness are not established.

DOOM is a later real-time evaluation and Product Hunt demonstration milestone:
the game must continue at normal speed while the assistant reasons. It does not
replace desktop task correctness. See [roadmap](../ROADMAP.md).

## Evidence ready for discussion

| Track | Verified result | Limit |
|---|---|---|
| [A1 exact unchanged observation](../research/observation_gating/REPORT.md) | 192 fresh real-app episodes, 96/96 success per arm, 1,446 exact frames; 17.15% same-trace image reduction | Scripted controller, zero model calls; local speedup unproven |
| [A2 exact tile transport](../research/observation_tiles/REPORT.md) | 64 fresh episodes, 32/32 success per arm, 553 exact frames; 70.73% same-trace serialized-byte reduction | Full images restored before viewing; not token savings; local speedup unproven |
| [PNG artifact preparation](../research/observation_tiles/IMAGE_ARTIFACT.md) | Two archived-trace validation replays: reuse saves 10.81% / 16.59% preparation time; level 1 adds 15.89% / 16.03% time reduction with larger PNGs | Offline component timings, not new GUI trials or model latency |
| Actual assistant use | Calc, Inkscape and two XTerm sessions completed by inspecting reconstructed screenshots and choosing actions | Exploratory demonstrations, not a randomized agent comparison |

The A1 and A2 percentages refer to different representations/controllers and
must not be multiplied into a cumulative token or speed claim. Raw failed
freezes are retained alongside successful ones. A2 revision 1 stopped at an
Inkscape baseline drag failure; revision 2 added observations during a planned
segmented gesture in both arms. It does not prove adaptive motor control.

## Most important finding for the next iteration

In the latest assistant-operated XTerm session, local action-to-image-ready time
was approximately 41–56 ms, but two command receipt timestamps were about
10.22 seconds apart. That interval includes inspection, reasoning and tool
boundaries. Further PNG optimization alone will not meet the actual objective.

Next implementation: persistent asynchronous execution with early feedback,
bounded held inputs, cancellation/release, explicit stale-state handling and
guarded local progress while the planner is waiting. This is **not implemented
yet**. The current `dogfood.py` reads stdin commands sequentially, despite
streaming early acknowledgments. Do not describe it as a concurrent runtime.

The next controlled evaluation must measure the actual agent loop, completion
quality and measured token use, not replace those with bytes or local timers.
No LLM API/token-metered comparison or comparable human baseline has run here.

## Parallel control-codec discussion

A remote [control-codec research branch](https://github.com/Unjuno/agent-interface/tree/research/control-codec-track)
was observed at `6d49811` during this publication review. It contains control
representation and design-thesis work. It is not merged or validated by this
publication. Keep executable semantics, lossless representation compression and
elimination of unnecessary decisions/boundaries distinct when discussing it.

## Reproduction and provenance

- Begin with [A1 usage](../research/observation_gating/README.md),
  [A2 usage](../research/observation_tiles/README.md) and their frozen protocols.
- Real applications ran in private Xvfb/Openbox sessions under Ubuntu/WSL2,
  using a Chromium-family Chrome for Testing binary, Calc, Inkscape and XTerm.
- Raw manifests contain historical machine paths/timestamps. They are evidence,
  not portable launch configuration; choose new output paths for new trials.
- `.gitattributes` preserves frozen research bytes across checkouts. The shared
  v1 Python source retains its measured CRLF bytes; invoke it with `python3`.
- Research source, packet/image evidence and negative runs are included. Generated
  caches/environments are excluded. No runnable release or Product Hunt launch
  is being published by this update.

For status claims, use [RESEARCH.md](../RESEARCH.md) and the primary reports, not
an unchecked roadmap box or an isolated successful screenshot.
