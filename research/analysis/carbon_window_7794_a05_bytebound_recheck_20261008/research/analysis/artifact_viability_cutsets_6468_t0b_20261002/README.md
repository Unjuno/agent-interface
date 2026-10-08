# #6468 T0b — fresh formal allocation after predecessor STOP

**Terminal disposition:** `SUBSUMED_BY_12` (synthetic method-only). See `REPORT.md` and append-only `RUN.json`. The predecessor allocation `6468-T0-ARTIFACT-VIABILITY-20261002-01` remains STOPped before candidate in Draft PR #6487. No outputs from that allocation are pooled into this one. T0b has its own candidate run, audit, and output identity.

## H / T / D / C / U

**H.** Under the two frozen synthetic artifact contracts, weighted partial checks can tie while one route fails an indispensable requirement and the other passes. Dependency minimal cut sets should preserve required-vs-cosmetic distinctions and UNKNOWN without improving any decision already made by a fully specified strict TaskContract.

**T.** Execute the finite frozen fixture exactly once with `candidate.py`, producing `raw_candidate.json`. The fixture contains two seven-check contracts and six paired cases (12 routes): document citation tie, spreadsheet formula tie, cosmetic-only failure, missing export, rendered UNKNOWN, and no-inversion control. A separate `auditor.py` invocation independently recomputes scores, strict status, dependency status, minimal cut sets and denominator from the frozen fixture, verifies citation/formula evidence, and runs five corruption controls (critical failure removal, UNKNOWN→PASS, citation-target swap, score double-count, cosmetic hard gate). No real document, office app, model, GUI, recipient, or network is involved.

**D.** `METHOD_PASS_SCOPED` requires both planted inversions and all controls to be detected, UNKNOWN preserved, all 12 routes and both contracts' full minimal cut sets reconciled, and every mutation rejected. Dependency-vs-strict decision mismatch must be zero to support `SUBSUMED_BY_12` (diagnostic-only cut sets). Any mismatch is `FAIL_METHOD`; no result from T0b applies to actual artifacts or route efficiency.

**C.** This synthetic fixture is authored, small, deterministic and self-scored. A strict required-effects contract can be equally discriminating. Minimal cut sets may only improve explanation, not decisions.

**U.** Human purpose, source credibility beyond explicit IDs, rendered pixels, spreadsheet engine behavior, real export/delivery, route execution, end-user usability and cost are not represented. No product/runtime benefit or real-world reliability inference is licensed.

## Freeze and environment

- Issue remains open; predecessor PR #6487 is Draft. T0b branch/path collision search was empty at freeze.
- GitHub `main` provenance at freeze: `518918b71599bf6d7fb662aaf6ae332e14d6132f`.
- Source and fixture are self-contained and pinned by SHA-256. They do not import repository code. A later `main` advance therefore does not change this allocation's scientific inputs; no post-freeze rebasing or source edits are allowed.
- Environment: Windows CPython 3.12.10, CPU-only, deterministic finite workload. WSL has nine active shared workers and #6389's owner has an active WSLc/native comparison gate, so no WSL/WSLc/Docker call is made. The test has no container/kernel dependency; no timing or memory benefit is claimed.
- One formal candidate command followed by one independent auditor command, no retry. `FREEZE.json` retains pre-run counters; `RUN.json` records post-run counts; raw results and manifest are additive to this successor path.
