# Reverse-order three-arm Calc comparison

This separately frozen block reverses the [eo01-eo03 block](../wslc_calc_three_arm_20261101): fresh ep01, compiled ep02, direct ep03. Each uses the same per-route input hashes and pass criteria as its counterpart, on the same fixed 472/615 Calc fixture. Main at freeze was 8591f398288a6a86b8aa8f51bd0d1580a29ac0e0; the source snapshot was unchanged from the preceding block. WSLc used a private Xvfb, 1 CPU / 1 GiB, no container network and one persistent gpt-6.1-sol low host session per route.

| order | route | task interval | launcher | calls | input (cached subset) | output | saved effect |
|---|---|---:|---:|---:|---:|---:|---|
| ep01 | fresh | 10.751 s | 15.781 s | 2 | 25,751 (12,160) | 140 | exact 472/615 |
| ep02 | compiled | 7.227 s | 9.579 s | 1 | 12,185 (8,192) | 78 | exact 472/615 |
| ep03 | direct | 6.071 s | 8.406 s | 1 | 12,185 (0) | 62 | exact 472/615 |

All three saved the exact two numeric cells and had verified release and neutral final X input. Compiled yielded SAFE_YIELD / effect_unavailable then saved through a fresh guarded continuation without entry replay. Fresh regrounded before Save; direct used current binding and expected-value OCR with guarded Ctrl+S.

Extract raw.zip beside audit.py and run python audit.py without optimization. compare.py, with both block directories present, re-audits all six attempts and checks matching per-route frozen input hashes and criteria, runtime manifest lists, six distinct owner sessions and eight distinct model-call IDs. Across the two blocks task medians are 6.258 s direct, 6.561 s compiled and 9.659 s fresh; input medians are 12,185 / 12,185 / 25,743 tokens. In the forward block compiled was faster than direct; in this reverse block direct was faster. Cached input is already included. Task timing excludes startup, fixture preparation and audit; launcher timing includes launched process startup but excludes preparation and audit. WSLc warned that the memory limit excludes swap.

These are two samples per route, on one layout and known values, using scripted Save and expected-value OCR, with unequal model calls and different cache/provider conditions. No population speedup, cost, general reliability, arbitrary edits, persistent obstruction, partial-input recovery, MAP01 completion or project completion follows. Raw candidates, captures, usage, receipts and FODS are retained; private model protocol journals are omitted. Earlier exploratory direct failures are separate and not silently counted in these blocks.
