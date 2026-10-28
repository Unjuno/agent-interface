# Docker/Xvfb MAP01 caller efficiency comparison

This packet compares the guarded direct keyboard route with the compiled caller on ViZDoom 1.3 / FreeDoom MAP01 under a pinned Docker Desktop Linux image and Xvfb. The direct and compiled arms use fresh matched seeds, counterbalanced order, one 600 ms W-forward action, independent X11 key-state sampling, a mandatory empty release receipt, one post-release environment synchronization tick, and a position/effect oracle.

See [aggregate result](RESULT.md). Raw arm observations, PNGs, bridge event/execution/release records, source/harness hashes, and per-attempt Docker logs are retained in `r10/`, `r11/`, `r12/`, `r13/`, and `r14/`. Each packet has pretrial and posttrial SHA-256 manifests. R10, R12 and R14 contain the six successful comparison pairs; R11 and R13 preserve pre-input harness failures and are excluded from timing.

The aggregate has six pairs and twelve passing task/effect/release arms. Compiled latency is slower in every pair; the median paired difference is +49.027 ms (+5.58%). This is small descriptive evidence scoped to this local Linux/Xvfb workload. It does not establish Windows/WSLc transfer, MAP01 completion, blocked-I/O recovery, product-level efficiency, or general reliability.

The runtime code change that enabled these keyboard tails was merged as PR #9796, commit `65edb4a7685bc9a6104965c294d612d4b34502c0`. Repository package tests passed 197/197 with two skips in both normal and optimized Python on the local Windows host. The two skips are environment-dependent.
