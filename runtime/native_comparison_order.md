# Native comparison arm order

`runtime.native_comparison_cli_v1 prepare` defaults to `--arm-order forward` (plain → ephemeral → persistent). For the paired order check, pass `--arm-order reverse` (persistent → ephemeral → plain), use the same seed, and give it a fresh private allocation. The registration and capture plan record the physical order. The runner, the per-arm clock audit, and the X11 lifecycle audit all use that order. The six tasks and the three-preflight, fourteen-grounding call budget remain the same.

The runner stops at the first unverified or failed arm and preserves its available evidence. A first-arm persistent failure can leave evidence of an individual effect while the matched comparison holds because its reference arms were unstarted. Each allocation permits one confirmed run. Reaudit a retained block with its original source revision and externally retained seal digests.

The opposite order tests sensitivity to the position of the two outer arms for this seed and fixture. Ephemeral is still in the middle in both blocks. Fresh planner threads and separate owned App Servers describe local session lifetime. Provider-side caching can carry over across those boundaries. Interpret usage using the reported input and cache fields.
