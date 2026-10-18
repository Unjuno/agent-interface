# A10 — native Xvfb V13 cleanup after alias refusal

**Outcome: `PASS_METHOD_SCOPED` (independent audit v2).** In one fresh isolated Xvfb case, `a` and `A` both resolved to keycode 38. The candidate-only uniqueness guard refused `up_batch` with `ValueError: distinct resolved keycodes required for up_batch`. V13 published a failed terminal, then its cleanup receipt reported `verified=true`, `keys_down=[]`, `keys_unknown=[]`; the release attempt observed keycode 38 down before KeyRelease and up afterward. An independent observer saw a neutral keymap, and Xvfb exited 0.

Raw SHA-256: `0dfa5d26e4939b376f66b971b32a89f4dc2a8f4abeacc91525b8b57bbc76992e`. `A10_AUDIT_V2.json` passes 7/7 direct evidence checks. The earlier `A10_AUDIT.json` STOP is preserved: its v1 auditor incorrectly required distinct owner admission rows that this API does not retain. The v2 auditor uses the specific refusal plus the cleanup receipt's key-down-before/key-down-after observations and the observer keymap; it does not rerun or modify the candidate.

The experiment uses native Xvfb, not a physical keyboard or GUI application. The duplicate-keycode guard exists only in the candidate copy. This does not establish application consumption, task effect, threat response, recovery benefit, latency bounds, or MAP01 completion. Issue #59's live gate remains unmet and unassigned.

The A07 and A08/A09 STOPs remain preserved as separate first outcomes. This is a new A10 allocation, not a retry of those runs. Sources are frozen to current main `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933` in `FREEZE.json`.
