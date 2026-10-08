# Recovery status — Issue #3983

**Disposition: HOLD_SOURCE_DELIVERY. This data-only recovery is not an independently re-audited or reproducible scientific PASS.**

This directory preserves the ten exact non-executable data, freeze, execution, report, and publication files from Draft PR #4015. The two raw parts restore a 3,352,631-byte `RAW.json` with SHA-256 `e5f0aea94203035be3ed52fd589b8f008b16d1a86dc2ffea98b48768fd5e8e56`; the compressed audit receipt restores 7,144 bytes with SHA-256 `0a80cbd946d0b2c7b306d711757dc4c08e28717778eb6a08b9d9dfa4bd790006`. These are storage-integrity checks only.

The frozen executable source/binary is absent from the remote branch and has not been recovered. Consequently this snapshot does not permit repository-based experiment reproduction or an independent rerun of the scientific auditor. Historical 24-case/12-pair outcomes and reported audit/control counts remain reported-only. No Xvfb, renderer, observer, formal case, or auditor was run as part of this recovery; no scope is promoted and no earlier allocation is changed.

Keep Issue #3983 open and the original Draft PR/source-delivery boundary explicit. If the exact frozen source is recovered, verify its FREEZE hashes before considering a separate re-audit. Do not infer production readiness, task correctness, or latency/token benefit.
