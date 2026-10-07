# Issue #7367 retained-workload byte-binding audit A02

**Result: `PASS_AUDIT_BINDING_REVALIDATED`.** The frozen v2 auditor re-audited the exact retained A01 raw output and reproduced the preserved A01 semantic audit byte-for-byte at the JSON value level. The workload bytes match A01 `PRE-RUN.json`, and the raw output matches its frozen SHA-256.

A construction mutation added an 8,192-byte padding field to the declared-dead `stale-summary` record without changing the graph or liveness set. The mutation updated the raw workload digest, record hash, and policy visible-byte counts to remain self-consistent. The original v1 auditor accepted the mutated workload and all its checks passed; v2 rejected it against the frozen A01 workload and raw digests.

The formal run used OrbStack with the pinned `python` image digest on `linux/arm64`, network disabled, and pull disabled. It ran once. Candidate invocation count was zero; the retained A01 candidate was not replayed. The machine-readable result is `formal_01/AUDIT_V2.json`, with its SHA-256 retained in `formal_01/SHA256SUMS.txt`.

This result establishes byte binding and semantic reconstruction only for the finite synthetic A01 artifact. It does not establish open-world workflow completeness, runtime or model behavior, context savings, quality, GUI behavior, or product utility. The freeze manifest is the trust anchor for these SHA-256 comparisons.
