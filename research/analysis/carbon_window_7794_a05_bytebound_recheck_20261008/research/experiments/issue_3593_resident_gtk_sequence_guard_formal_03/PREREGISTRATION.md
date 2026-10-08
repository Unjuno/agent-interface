# Issue #3593 formal GTK allocation — successor 03

Allocation 01 STOPped before formal invocation because the fixture path in the runner did not match the frozen tree. Allocation 02 invoked the runner once but STOPped at Python module import before any GTK row began. Both STOP records remain immutable at their respective paths; neither produced experimental rows.

Allocation 03 corrects startup by explicitly adding read-only source root `/src` to Python's import path. The policy code, trace schedule, GTK fixture, expected effects, and acceptance gates are otherwise unchanged. Construction tests are 6/6 and the independent audit corruption self-test is 4/4. OrbStack preflight separately confirmed GTK3/Xvfb, one synthetic Space press/release, visible title effect, and raw frame retrieval; this is setup evidence only.

One formal invocation, zero retries: nine exact traces × two policy candidates × effect on/off = 36 fresh GTK/Xvfb rows. PASS requires independent replay, per-prefix visible effects, effect-off controls, rollback contrast, positive controls, key release, raw-frame hashes/dimensions, process reap evidence, and independent audit. Pinned image `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27` (`linux/arm64`), no network, read-only source, fresh writable evidence.
