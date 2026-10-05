# A05 result: current-source shared-display one-key `up_batch`

A05 ran the one-key batch API through the exact PR #7974 source frozen at `b5fbfed1c896f587dd5dfeb30c2735d63f670264` over main `2f2c83c3da36566bac410b13b2ed5202c9641f1a`. The single-owner control produced server keymap `false → true → false` and an owner-verified one-item `up_batch` receipt. In the pair, distinct owners and leases both admitted W; after A's verified `up_batch(['W'])`, the server-global keymap was false while B's local `owned_keycodes` still contained 25. B's one-item batch receipt then verified and final global state was neutral. Candidate and frozen raw-only auditor each ran once and exited 0.

This confirms that the current-at-freeze one-key batch receipt describes shared X-server state, not owner-isolated held state. It supports the exclusive-display/cooperative-arbiter precondition. A03 independently found the same condition through the prior single-key `up` API. A04 was stopped before candidate start because main and PR head moved after its freeze; it remains 0/0 and is preserved.

A05 uses one key per `up_batch`. It does not test ordering across multiple explicit UPs in the full V15 release-batch backend. It is not physical-key, production display, application, GUI, game, task-effect, threat-control, recovery, or MAP01 evidence.

Raw: `results/A05/raw.json` (SHA-256 `8ae6eba113ae56d4bc7fd636340d5177ab0f2329e6955c3d65468774d4eb5c11`). Auditor output: `results/A05/audit.stdout` (SHA-256 `fbe8137a9384fd61faf922f765d442390f001318127b11624c75a2844e109f5a`). All transported output hashes are in `results/OUTPUT_SHA256SUMS`.
