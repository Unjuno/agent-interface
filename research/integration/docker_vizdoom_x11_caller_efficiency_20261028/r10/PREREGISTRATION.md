# Docker/Xvfb direct-versus-compiled X11 caller comparison R10

Fresh matched comparison after diagnosing the stale-effect-oracle issue. R9 showed the W-forward action changed MAP01 POSITION_X by +127.538 after one ASYNC_SPECTATOR tick, while the compiled/direct callback had read before that tick and recorded false. The post-release synchronization tick must occur before the effect predicate and typed effect receipt.

Four one-shot counterbalanced arms: pair 1 direct then compiled, pair 2 compiled then direct. Fresh pair seeds 2026102911 and 2026102912. Exact same source candidate, Docker image, Xvfb, setup, four bindings, 600 ms action, per-key release, terminal release, and local position oracle. A wrapper marks the environment tick pending only after the guarded keyboard route returns; the next post-action perception drains exactly one `game.advance_action(1, True)` and then reads position. Thus the same endpoint contains the tick, observation and effect verification in both routes. Initial setup tick is identical and outside timing. W-down is sampled independently; terminal verified-empty release and independent X-up are required.

Per-arm PASS requires task route completion, independent W-down, verified empty release, independent W-up, position delta >=0.1, and successful effect receipt. Failures are retained, never rerun. Compare the two paired latency differences descriptively; n=2 cannot establish general speed or reliability. No model/provider/MCP call or usage accounting.

Runtime scope: Docker Desktop Linux Engine + Xvfb + FreeDoom MAP01 only. No Windows, WSLc, blocked-I/O recovery, MAP01 completion, broad reliability or product-efficiency claim. Network none, read-only rootfs, read-only source, writable evidence, `/tmp` cwd.
