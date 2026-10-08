# Issue #6624 T0 — operational representation contrast

Disposition: `METHOD_PASS_SCOPED`.

This additive successor directly addresses the identified #6610 T0 assay weakness. Six finite rows cover no follow-up, a spreadsheet source-cell increment, and a drawing title replacement, each with a pixel-only control where applicable. In both families the initial renders are exactly equal. The static spreadsheet state contains only visible pixel/value entries—no formula key or cell dependency model. The structured route contains addressable cells and `=A1+A2`; after changing A2 from 3 to 4, the candidate recomputes TOTAL from inputs as 6. The static drawing retains only a raster mapping, while the structured drawing exposes addressable elements; title replacement therefore stays `UNKNOWN` for flat and updates only `title` for structured. Pixel patches remain achievable on both routes.

The independent raw-only auditor reconstructed the complete six-row output without importing candidate code, rejected all seven corruption controls (injected answer, hidden structure, wrong target, collateral mutation, false formula, pixel-only editability claim, and strengthened initial contract), and reported zero errors. The separate cost model yields weighted illustrative operation units of flat 4.8 vs structured 4.2 for spreadsheet, and flat 4.4 vs structured 4.2 for drawing under the authored mixture. Those numbers are assumptions for assay sensitivity only—not observations, measured time/effort, a population estimate, route recommendation, or scientific evidence of user benefit. Correctness gates and cost are reported separately.

## H / T / D / C / U

- **H:** A literally pixel/value-only route and a structured formula/element route can have byte-for-byte equal initial render contracts while structural follow-ups yield UNKNOWN versus independently computed effects; pixel-only follow-ups remain achievable on the flat route. A separately declared cost mixture may reverse initial-cost ranking, but only as abstract sensitivity.
- **T:** Frozen six-row synthetic state-machine test; two representation families × structural/no-change/pixel-only strata; candidate and auditor each ran once in separate network-disabled WSLc containers; retries 0. Construction suite ran on host before freeze, 6/6 passed.
- **D:** `METHOD_PASS_SCOPED`: six exact roster rows independently reconstructed, equal initial render, no hidden structure in flat states, structural flat outcomes UNKNOWN, structured effects exact, pixel patch available on both, 7/7 mutations rejected, independent mixture arithmetic reproduced.
- **C:** The state machines and cost units are authored abstractions. Pixel/value-only states are not real codecs/files; the future-change mixture is illustrative and not estimated from users.
- **U:** No real spreadsheet/drawing app semantics, file compatibility, human editability, follow-up prevalence, time/effort, model behavior, safety, or product benefit. No GUI, model, GPU, real/user artifact, or network use.

## Frozen source and execution evidence

- Intake main recorded in `FREEZE.json`: `80c6a26898d72a2bec49055cafd0626d93f1c2d0`.
- Branch: `research/representation-contrast-6624-t0-20261002`; additive path: `research/analysis/representation_contrast_6624_t0_v1/`.
- Source SHA-256: fixture `81a2eedb7f03514d49f1656e7f72b5c199dd176653b52cfc10e106d3b9a2c340`; candidate `2c6a2dfb6fa9f5f1bae98b1727e412d771351509ff370cf4eeb7ae4509dd7df5`; audit `3a7cef12abdd79b04fff28bec24c40df9397a2547ae221c9cedb1c1141535a53`; tests `6f6553892949cc2adbf3a866e346c3c2f0fdc507d236107c835fba87a1ba2ac7`.
- Runtime: Microsoft WSL Containers (`wslc.exe`) 3.0.1.0; image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`; linux/amd64; Python 3.12.14; pull never; network none; source read-only; dedicated output mount. Candidate and auditor were separate invocations; both exited 0.
- Exact candidate command: `wslc.exe run --pull never --rm --network none --cpus 0.25 --memory 256m --mount type=bind,source=<frozen-source>,target=/src,readonly --mount type=bind,source=<dedicated-results>,target=/out --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B candidate.py /src/fixture.json /out/raw.json`.
- Exact independent audit command: same frozen container boundary in a fresh invocation, ending `python -B audit.py /src/fixture.json /out/raw.json /out/audit.json`.
- Both invocations warned: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The memory setting was requested; effective memory/swap enforcement is not claimed.
- Candidate raw SHA-256: `6c23e0aaf048bb4e50345c0a7528f8d5999974431040fcefe7114a20f345a723`. Audit SHA-256 is recorded in `RESULT_METADATA.json`.

## Construction history retained

Before formal freeze, the host-only suite caught and retained several construction failures: an invalid spreadsheet pixel-patch state lookup; a drawing raster-patch shape mismatch; a `formula: null` field that meant the flat route still retained the formula schema; an initially ineffective strengthened-contract corruption check; and a candidate/oracle state mismatch. Each was corrected before freeze. The final pre-freeze construction suite passed 6/6. None of these construction attempts invoked the frozen formal candidate or auditor.
