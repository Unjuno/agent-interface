# #1262 first outcome — 20 Hz full process-tree CPU accounting

Task `TEMPORAL-BUFFER-X11-PROCESS-TREE-CPU-BATCHED-20260918-002`.

## Decision

**PASS_20HZ_PROCESS_TREE_CPU_BOUNDED_SCOPED**

Fresh orchestration-only successor to #1258. Exact scientific runner/fixture/audit and all CPU/capture/callback gates were held fixed. Predecessor partial rows were pooled0. Formal used 8 fresh matched pairs /16 private X11 sessions, one pair per bounded outer invocation; same-pair reruns/replacements/tuning0.

## Measurements

- candidate total owned process-tree CPU fraction: **0.042152..0.070234**; frozen per-arm gate <0.15;
- paired median candidate-minus-baseline process-tree CPU fraction: **0.035323**; gate <=0.05;
- maximum paired CPU delta: **0.048125**; gate <=0.10;
- capture count: **31 in every candidate arm**; dropped slots0; capture exceptions0;
- capture p95: **2.007..2.944 ms**; gate <10 ms;
- peak raw ring:11 frames in every candidate arm;
- callback-count ratio median: **1.000000**; gate [0.97,1.03];
- callback p95-gap median increase: **0.021420 ms**; gate <=2 ms;
- cleanup: all 8 pair markers/files present, pair IDs unique, no remaining owned Xvfb/Tk/runner process or private X11 socket.

This closes the explicit #1093 accounting limitation for this scoped fixture: runner-only CPU was about 3% in candidate arms, while adding Xvfb/Tk raised total owned process-tree CPU to roughly 4.2–7.0%. The total remains inside the frozen local CPU envelope.

## Integrity

Source-first canonical 3-part transport exactly matched local Git object identities before formal. The earlier single-file transport is retained as rejected/noncanonical provenance and was not used. Frozen audit: PASS/errors[]. Orchestration audit: PASS/errors[]. Postformal source rehash: PASS. Copied-result corruption controls reject5/5.

FORMAL_RESULT SHA-256 `8c4cf01025a9ba8baca18e65159e500305ba2fce4bfca670fcd79a376c6cd0b3`.
AUDIT SHA-256 `53494363f3eabe6f883f95589b07e6c870818344b442bbe34d177df8349f756e`.
ORCHESTRATION_AUDIT SHA-256 `1781520ccc598ff36d97710b8338de2ad5c5276b5b267fb691b29edfc360dbbe`.
CORRUPTION SHA-256 `93a361f96e90df751e0703253bc193834903886478b1fa01c9b9e4caac6fa77b`.

Raw FORMAL_RESULT is retained losslessly as deterministic gzip(mtime=0)+base64 and can be reconstructed without rerunning formal cases.

## Boundary

This is one Linux private-Xvfb/Tk 320x240 workload. `/proc` process CPU does not include uncharged kernel work, energy, compositor/GPU costs, or arbitrary desktop capture. It does not establish model value, task correctness, token savings, human tempo or production performance.
