# Reverse-order three-arm temporary-obstruction comparison

This separately frozen WSLc block reverses [eq01-eq03](../wslc_calc_three_arm_obstruction_20261101): fresh er01, compiled er02, direct er03. The per-route frozen candidate hashes and pass conditions are identical. Each arm uses the 472/615 Calc fixture, gpt-6.1-sol requested low with its own persistent host session, private Xvfb, 1 CPU / 1 GiB and no container network. The test itself adds an 8x8 target overlay after the first grounding, detects changed pixels before mint/program, removes its own overlay and regrounds on a fresh capture.

| order | route | task interval | launcher | calls | input (cached subset) | output | saved effect |
|---|---|---:|---:|---:|---:|---:|---|
| er01 | fresh | 11.155 s | 16.235 s | 3 | 40,650 (33,280) | 186 | exact 472/615 |
| er02 | compiled | 10.535 s | 12.859 s | 2 | 25,751 (20,352) | 140 | exact 472/615 |
| er03 | direct | 10.191 s | 12.593 s | 2 | 25,751 (20,352) | 140 | exact 472/615 |

All three saved the exact two numeric cells with no formulas, verified action and owner release, and recorded neutral final X input. Compiled yielded SAFE_YIELD / effect_unavailable then continued to guarded Save without replaying entry. Extract raw.zip beside audit.py and run python audit.py without optimization and with Pillow. With the prior directory present, compare.py re-audits both blocks, checks candidate hashes and pass criteria by route, distinct owner sessions and model call IDs, and reports all six attempts. Across both blocks, task medians were 9.278 s direct, 10.150 s compiled, 12.096 s fresh; median input tokens 25,751 / 25,751 / 40,666. Cached input is included. Task timing excludes startup, fixture preparation and audit; launcher timing includes launched-process startup but excludes preparation and audit.

Main at freeze was 04d72a6b29e22ab059464d266bfc95392c908494; the source snapshot was unchanged from the preceding block. Raw candidates, captures, usage, action receipts and FODS are retained; private model protocol journals are omitted. WSLc warned that memory limits exclude swap.

Two fixed-order samples per route on one fixed layout and values, with test-controlled obstruction that the test removes, expected-value OCR and scripted Save, do not establish general speed, cost, reliability, persistent-obstruction recovery, arbitrary edits, partial-input recovery or MAP01 completion. The caller detects stale pixels; this is not a runtime stale-handle refusal. Provider/cache conditions and route internals differ, and fresh intentionally has an extra model call.
