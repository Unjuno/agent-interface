# Agent Interface — Research Preview 2

This is an **experimental research snapshot**, not a production-stable runtime release.

`v0.0.1-research.2` is the first recommended public research snapshot. It supersedes `research.1` for citation and benchmarking because the initial publication exposed two transcription errors in the v3 human-readable report and a non-canonical v1 CSV serialization. The raw conclusions were re-audited and the corrected report now points directly to the published summary CSVs.

## Included evidence

- **Real Apps v1:** XTerm, Chromium, LibreOffice Calc, and Inkscape; fixed-wait vs sparse/reactive control; input-delivery pacing experiments.
- **Real Apps v2:** semantic-method lifetime separated from optimized-route lifetime.
- **Real Apps v3:** Guarded Hierarchical Deoptimization, including focus, geometry, binding drift, and pre-execution route guards.
- Architecture and methodology notes.
- Raw summary CSVs shipped with the same release bundle.
- GitHub Pages research landing page.

## Current promoted conclusions

- correctness remains a hard gate;
- semantic knowledge should outlive stale route/binding optimizations;
- observable fast-route dependencies should be guarded before executing predictable failure paths;
- route reheating after two clean fallback uses remains the current baseline;
- the next research focus is **Observation Gating**: suppressing model-visible images when no relevant new visual information exists.

## Important limitations

- current real-app evidence is Linux/X11;
- local harness timings are not LLM-in-loop latency;
- planner bytes are not token counts;
- observed pixels are not image-token counts;
- automatic general method discovery is not a finished feature;
- APIs and algorithms are expected to change rapidly.

See `RESEARCH.md` and the reports under `research/` before citing performance numbers.
