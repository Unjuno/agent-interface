# Three-arm Calc comparison with temporary target obstruction

A fresh prospectively fixed WSLc block compares direct, compiled and fresh routes in that order on the 472/615 Calc task. After each first model grounding, the test covers the target with its own 8x8 overlay, observes changed target pixels before any mint or program, removes the overlay, captures again and makes a new grounding call. The caller detects the stale pixels; this does not claim a runtime stale-handle refusal. The three routes then use guarded entry and Save, with expected-value OCR. Compiled yields SAFE_YIELD / effect_unavailable and continues without entry replay; fresh makes one additional post-entry model call.

| order | route | task interval | launcher | calls | input (cached subset) | output | saved effect |
|---|---|---:|---:|---:|---:|---:|---|
| eq01 | direct | 8.365 s | 13.328 s | 2 | 25,751 (12,160) | 156 | exact 472/615 |
| eq02 | compiled | 9.765 s | 12.093 s | 2 | 25,751 (19,968) | 140 | exact 472/615 |
| eq03 | fresh | 13.037 s | 15.391 s | 3 | 40,682 (25,472) | 202 | exact 472/615 |

All three saved exactly the two numeric cells with no formulas, had verified action/owner release and final X input neutral. The auditor independently recomputes the before/obstructed crop hashes from retained captures, checks the recorded absence of prior mint/program, verifies the later model request refers to a newer capture, associates all model requests and responses with image bytes, and checks the FODS and release receipts. Extract raw.zip beside audit.py and run python audit.py without optimization and with Pillow. Raw candidates, captures, model usage, action receipts and FODS are retained; private model protocol journals are not included.

Main at freeze was d24b6ff1fb560e7ea0be35f4e7b8281c4a4e6f7a; relevant runtime and named model-client files were checked in the preceding block and only evidence changed since. Each arm uses a separate persistent gpt-6.1-sol low host session, private Xvfb WSLc container with 1 CPU / 1 GiB and no container network. WSLc warned that the memory limit excludes swap. The predeclared rule was one attempt per route without success retry. Task interval excludes startup, fixture preparation and audit; launcher includes launched-process startup but excludes preparation and audit. Cached input is included in input tokens.

One fixed-order block, one fixed layout/value pair, a test-controlled obstruction that the test itself removes, expected-value OCR and scripted Save cannot establish a general speedup, reliability, cost, recovery from a persistent obstruction, arbitrary edits, mid-input failure or MAP01 completion. Provider/cache conditions and route internals differ; fresh intentionally makes one extra model call. The raw stale precondition record is retained alongside the independently checked images; it is not an atomic history of every possible native action.
