# Agent Interface — Research Preview 1

This is an **experimental research snapshot**, not a production-stable runtime release.

## Why this release exists

The repository is being used as both the public research record and the release channel for Agent Interface: a proposed local systems boundary between strong AI planners and computer I/O.

This snapshot freezes the evidence behind three research iterations so results can be reproduced and compared against later changes.

## Included evidence

- **Real Apps v1:** XTerm, Chromium, LibreOffice Calc, and Inkscape harnesses; fixed-wait vs sparse/reactive control; input-delivery pacing experiments.
- **Real Apps v2:** semantic-method lifetime separated from optimized-route lifetime.
- **Real Apps v3:** Guarded Hierarchical Deoptimization, including focus, geometry, and binding drift experiments.

## Current conclusions

- correctness should remain a hard gate;
- semantic knowledge should outlive stale route/binding optimizations;
- observable fast-route dependencies should be guarded before executing predictable failure paths;
- the next research focus is **Observation Gating**: suppressing model-visible images when no relevant new visual information exists.

## Important limitations

- Linux/X11 only for current real-app evidence;
- local harness timings are not LLM-in-loop latency;
- planner bytes are not token counts;
- observed pixels are not image-token counts;
- automatic general method discovery is not a finished feature;
- APIs and algorithms are expected to change rapidly.

See `RESEARCH.md` and the reports under `research/` before citing performance numbers.
