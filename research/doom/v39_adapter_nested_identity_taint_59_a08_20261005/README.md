# V39 malformed outer identity taint — A08

## H / T / D / C / U

**H.** A malformed outer key or token can be rejected as `identity_unavailable` before the projector reaches the intact nested adapter identity. If the original valid group remains paired, malformed telemetry can still leave timing exposed.

**T.** Freeze baseline source at exact PR head `aa88a9d95e208d413e64a23fe30754ec52c9ad55`, candidate/test hashes, and retained A01 fixture. Mutate a duplicate DOWN row's outer `intent_token` and `key`, each to null and a list. Compare exact projector behavior and run the preceding A05/A06/A07 regression methods.

**D.** Baseline must retain paired timing for all four mutations. Candidate must emit `identity_unavailable` and exactly one incomplete adapter receipt with both intervals null, and pass all six targeted methods. The separate raw-derived auditor replays each mutation.

**C.** Candidate records an actuation-fingerprint conflict from valid nested fields before returning for invalid outer identity; previously collected groups with that fingerprint are tainted after the scan.

**U.** Deterministic source-projector tests against one retained synthetic adapter trace only. No live input, application consumption, useful feedback, threat response, bounded recovery or MAP01 completion is established. The pinned WSLc image ran without network; runtime warned swap/cgroup support was unavailable, so full memory/swap enforcement is not claimed.

Runner and auditor terminal outputs are retained byte-for-byte in gzip files.
