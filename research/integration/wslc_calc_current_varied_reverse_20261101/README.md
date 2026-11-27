# Reverse-order current-runtime varied-value Calc pair

This is a separately frozen reverse-order counterpart to [em01/em02](../wslc_calc_current_varied_472_615_20261101). It uses the same per-route candidate input hashes and 472/615 fixture, but runs fresh first (em03) and compiled second (em04). Both allocations use one persistent gpt-6.1-sol low session, private Xvfb, WSLc 1 CPU / 1 GiB without container network, and separate host model calls. As before, the initial pixel reference is stale, expected-value OCR is used, and Save is scripted.

| allocation | route | task interval | launcher | calls | input (cached subset) | output | effect |
|---|---|---:|---:|---:|---:|---:|---|
| em03 | fresh | 8.620 s | 13.641 s | 2 | 25,735 (20,352) | 124 | exact 472/615 |
| em04 | compiled | 6.894 s | 9.328 s | 1 | 12,185 (0) | 78 | exact 472/615 |

Both saved FODS documents have exactly the expected cells and no formulas. Owner release and independent final X key/button state are neutral. The compiled path yielded SAFE_YIELD / effect_unavailable and continued through guarded Save without replaying entry. Extract raw.zip beside audit.py and run python audit.py without optimization. Raw captures, receipts, candidates, usage and saved files are retained; private model protocol journals are not included.

Running compare.py with both archive directories present re-audits all four attempts, checks matching per-route input hashes, matching runtime manifest lists, distinct owner sessions and distinct model call IDs. The compiled versus fresh median task intervals were 6.687 versus 9.599 s; median input tokens were 12,185 versus 25,743, including cached input. Task timing excludes startup, fixture preparation and audit; launcher timing includes launched process startup but excludes preparation and audit. WSLc warned that the memory limit did not include swap.

Two ordered pairs on one fixed layout, scripted Save and known expected-value OCR do not establish a general speedup, reliability, cost or arbitrary-value competence. Cache states and route internals differed, and fresh used one additional model call by design. This is not persistent-obstruction, partial-input or third-arm validation; it does not establish MAP01 completion. The earlier source was checked against main be0cae0a635e5852924a12c8ae971044cc0ce276; only evidence files changed on main before this reverse pair was frozen at c53bf58dfd4eaba9995b0fa24b0c0079a156cf5a.
