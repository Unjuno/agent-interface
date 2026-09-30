# Recovery status — Issue #4297

**Disposition: HOLD — formal evidence package incomplete. This is not a verified PASS.**

This directory preserves the oldest owner branch's frozen source, plans, reported result, publication manifest, and the one recovered legacy evidence part. It does not establish that the reported formal result is independently reproducible from Git.

The original branch `research/x11-server-grab-liveness-20260923` at `04992797eca5fd5ae0c80213a47035a47fffce19` declares 36 `COMPACT16.part000..035.b64` files for XZ SHA-256 `c5f15b9165dd54d6ec72ec05c3e172beea39b6515002541946950c650bd78435`. Its tree and full path history contain only `evidence_parts/COMPACT.part014.b64`; none of the 36 declared files is present. Therefore the reported 15/15 formal rows, raw-only audit, and corruption controls cannot be reconstructed or independently rerun from the published package.

No experiment was rerun and no formal outcome was altered during this recovery. The source capsule remains useful for future, separately allocated work, but it does not replace the missing raw evidence. The later `20260924` branch is recorded by Issue #4297 as a parallel duplicate and is not a substitute for the original owner's evidence.

Do not use this recovery to claim production latency/SLO, broader platform behavior, or a validated scientific PASS. If the exact originally frozen evidence parts are recovered, verify all declared hashes and restoreability before reconsidering integration. Until then, retain the historical reported result as reported-only and keep Issue #4297 open/HOLD.
