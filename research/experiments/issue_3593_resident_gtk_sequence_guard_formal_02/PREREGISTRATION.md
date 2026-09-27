# Issue #3593 formal GTK allocation — successor 02

Successor to formal-01, which STOPped before formal invocation because its frozen runner referenced the fixture at the wrong path. No formal row was run in allocation 01; its STOP record is retained unchanged.

Formal-02 uses the corrected `/src/formal/fixture.py` path. OrbStack preflight exercised GTK3, private Xvfb, Space press/release, visible title change, and raw frame retrieval; this is environment setup evidence only.

One invocation, zero retries, 36 fresh rows: nine exact traces × two actual policy candidates × effect on/off. Each event is stepped individually; each emitted action is delivered before the next event. PASS requires independent prefix replay, visible GTK effects per prefix, effect-off controls, stale rollback contrast, positive controls, key-up, byte/hash/dimension image checks, process incarnation/reap evidence, and auditor corruption challenges.

The pinned image is `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27` (`linux/arm64`); network disabled, source read-only, fresh evidence writable. Source main commit `bec31389157ae5237bcc6474dfd9bf9b16d30752`. Formal outcome has not yet been observed.
