# PR #4474 review disposition

The automated review found that formal v3's auditor did not enforce the complete case matrix, terminal/release/score invariants, and its provenance gate trusted plan booleans rather than the captured receipt identity. Both findings are valid. The v3 files and raw evidence remain unchanged as historical output, but v3 is no longer considered a qualified PASS.

Formal v4 is a new allocation. It derives session binding from a runner-assigned identity attached to each event in the live subprocess stream, derives sequence/hash/image linkage from paired typed and pixel observations, and exercises stale, cross-session, and incomplete receipts using actual retained receipts. The independent audit enforces exact case IDs/count, terminal/release/score invariants, event-stream bindings, image hashes, and recomputed MAE/verdicts. The mutation check requires empty, truncated, unsafe terminal/release/score, and cross-session-corrupted results to be rejected.

The eventual issue disposition must be based on v4 only. Do not merge PR #4474 until this review response and v4 evidence are checked against the updated head.
