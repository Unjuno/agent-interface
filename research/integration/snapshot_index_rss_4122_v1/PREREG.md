# Public hash preregistration for Issue #4161

Formal allocation count: **0**.

- Base main: `118b385697a03be6452249bf2a0111718d7535c2`
- Branch: `research/snapshot-index-rss-4122-20260923`
- Allocation: `snapshot-index-rss-4122-20260923-01`
- Exact eager Git blob: `0e32e820f49d87181dc61420f0c5003128a6e90f`
- Exact reader Git blob: `ea72c166c2cea511ea91031dfbb14563fe4e3245`
- FREEZE.json SHA-256: `75d197e2203e932386db0be6da4d3f291a5f403987b383a0b4308452971ba50c`
- Complete local preformal source patch SHA-256: `82203f4122aba43dd1981ef8a4b91e0932a0d0d3c055ef5c2103c59b96dd7909`
- Fixture manifest SHA-256: `3f78e0831b3c0bb9236238e0633a4c6cee23599fd1ccc485fad59f9561b188e5`

The local patch hash commits to the complete preformal source, plan, environment, independent auditor, tests, inherited exact sources, construction note, and fixture hash manifest. Full source/raw bytes will be published after the consumed formal allocation; this commit is the preformal hash/gate commitment, not a claim that all bytes are already repository-accessible.

Construction failures are excluded and retained. Formal source bytes must match the SHA-256 table in FREEZE.json. Formal reruns/replacements/tuning: 0.

Decision gate: PASS only if matched-control effect(8192)-effect(128) is >=1,048,576 bytes for both Linux `smaps_rollup:Rss` and `Private_Dirty`, with all 30 rows/process/source/semantic/audit gates complete. Otherwise apply the typed HOLD/FAIL/STOP dispositions in FREEZE.json.
