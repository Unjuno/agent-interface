# Technical peer raw spot-check: V15 native executor composition

This is a technical peer saved-raw spot-check. I authored the native driver; this is not a non-author review or merge/quorum vote. I did not rerun the driver or auditor.

The pinned source head is `daa156edd8df541dfe0192c3f6f0c69b36b92fa2`. The retained source lock has 81 files; all 39 loaded module hashes match that lock, and the raw's complete before/after source maps match it. Raw SHA-256: `6d7b7acc4fcbb5b5b01e10affbd2e55711549819309f13b01d4460858550cd21`. The retained frozen audit reports 337/338 checks, with the sole failure `only_loopback`.

The core event trace is coherent across the three actual `ExecutorV13.submit` / `Backend.execute(hold)` cases:

- `ordered_normal` completed. The independent X observer saw `a,s,w` keydown in admission order and `a,w,s` keyup; the backend release rows have that same UP order at batch positions 0, 1, 2. Each confirmed UP measurement joins its own DOWN actuation identity. The keymap went from neutral to all three keys down and back to neutral.
- `cancel_hold` had `a,s` down in the observer keymap before cancellation. Event serials show `cancel_requested` (36), verified `input_released` (37), incomplete late-UP receipt rows (40, 41), then cancelled terminal (42). The cleanup measurements in the verified cancellation record match both admitted identities, classify as confirmed physical UP with `per_key_cleanup_snapshot`, and grant no authority. The late batch does not become an ordinary release certificate. The keymap is neutral after terminal.
- `follow_on` completed after the prior worker joined and the executor slot became inactive. It has a distinct intent token and actuation identity; its `w` DOWN/UP pair verifies normally and the final keymap is neutral.

The owner’s final records include a verified empty `close`; the raw reports executor close succeeded, no release watcher or owner thread remained alive, Xvfb exited 0, and no native events remained after teardown. The raw audit checks all 16 observation epochs against the recorded PNG RGB hash and 640x480 geometry. The artifact inventory contains one retained PNG reused for those epochs, plus 16 AIT files.

Qualification remains **failed as a whole frozen gate**. The private network namespace reports `lo`, `tunl0`, `sit0`, and `ip6tnl0`, so the frozen `only_loopback` predicate correctly fails. The raw does not record device flags or routes; those interface names alone do not establish usable connectivity or its absence. I therefore confirm the executor/key-identity evidence above as observed in this Xvfb run, but do not assign a PASS classification or claim network isolation beyond the recorded namespace and cgroup values. Deleting that failed predicate would not turn this retained run into a passing frozen audit.
