# A02 source-attribution audit

This read-only source audit resolves whether the two `query_keymap` calls between the key-up injections in `map01_v39_perkey_bridge_a02_20261005` contradict the current V39 release-order contract. The initial A01 construction and its audit are retained as `results/source-audit-a01/`. A02 adds a stronger per-key probe-order assertion but retains a candidate `FAIL_SOURCE_ATTRIBUTION` because its first version accidentally selected a down-edge sample; the failed raw is preserved in `results/source-audit-a02/`. A03 restricts that assertion to the historical owner's explicit-up branch. A04 verifies that A02's harness resolves the historical dependency owner path. A05 verifies by AST containment that the sole current production `query_keymap` call is inside terminal `release()`. Its first independent audit failed because the auditor compared nodes from separate AST parses; `audit.json` preserves that failure and `audit-v2.json` is the corrected raw-only audit.

## H/T/D/C/U

- **H:** The A02 trace comes from its injected V12 physical-edge fixture, not the current V39 V15 production source closure. The current closure performs explicit `XTest KeyRelease`/`XSync` calls per key, then one owner-state sample after the release batch; it does not query physical key state between explicit key-ups.
- **T:** Freeze main `69dd261430cb1ed875f5a76411c4a2a54777c114`; hash the A02 freeze/composition/trace, the injected V12 dependency and adapter, and the current V15/backend/V4/V3/V12 source chain. Parse the retained A02 trace and use AST/source-path assertions to distinguish the two closures. Run one candidate audit and one independent raw/source auditor.
- **D:** `PASS_ATTRIBUTION_ONLY` requires exactly two key-up injections with the retained two keymap samples between them; the A02 harness must load the historical dependency tree and must omit current V15/V4 source from its freeze; V15 must select the production release-batch backend and V4→V3→current `live_control/input_owner_v12.py`; current owner `query_keymap` must appear only in terminal `release()` cleanup, and explicit up must issue KeyRelease+sync without a keymap query.
- **C:** This resolves source attribution only. It does not run the A02 candidate again or exercise the full V39 session, a live X server, GUI, OS input, game, model, or application effect.
- **U:** The production path still has no per-key physical key-state measurement. Its per-key XSync receipt is not proof that the target application consumed the release. No latency bound, threat response, recovery, or MAP01 result follows.

## Reproduction

From the repository root, run the source-attribution A05 candidate, then its corrected independent auditor v2:

```sh
python3 research/doom/map01_v39_perkey_bridge_source_audit_a01_20261005/run_audit.py
python3 research/doom/map01_v39_perkey_bridge_source_audit_a01_20261005/audit.py
```

The existing A02 package and its frozen result files are read-only inputs. The audit output is new and additive.
