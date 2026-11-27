# R281 raw and independent audit — 2026-11-21

## Source and custody recheck

- Frozen against current main `381a21ace42891c2cd1e9cff3e231bec763ec2ba`.
- Independently recomputed all 41 Git blob IDs in the archived `SOURCE_VERIFY.json` against that commit: 41/41 matched.
- The original packet's SHA-256 manifest verifies 10/10 entries, including the raw archive. Archive SHA-256: `248662bc4109662568b2a8ca09a0efe98c97b78d727474a3ccee9be3eca9738e`.
- The archive contains 32 members. A path/link audit found no absolute/traversal paths and no symlinks or hardlinks. The raw event stream and owner journal inside the archive match the separately retained raw copies.

## Independent event adjudication

The raw event stream contains 38 events, including seven typed observations. It starts at sequence 1 with ammo 50 / health 100. The first distinct intent admits `Right`, then reaches `expired` with zero completed steps. Its delayed `Space` step never starts. The owner journal separately records an expiry release with verified empty buttons/keys and no unknown keys or errors. The owner verification timestamp is 213730102104346 ns versus deadline 213730101020188 ns: 1,084,158 ns (1.084 ms) after expiry. The terminal embeds release verification, but the standard event stream has zero standalone `input_released` events.

Only after that terminal, a new recovery ID performs an observe-only operation at sequence 4, still ammo 50 / health 100, and completes with release verified. A third ID then admits exactly one `Space` attack. Sequence 7 reports ammo 49 / health 100; the archived image `raw/007.png` shows the attack flash and ammo 49, while `raw/001.png` shows the initial ammo 50. Its terminal release and final owner close are verified neutral. The runner exits 0.

## What this proves and what it does not

This is one bounded live MAP01 result: an expired intent's stale delayed action was suppressed, neutral input was independently observed, a fresh observation was taken, and a separate task action produced an observable ammo decrement. The audit's post-control score says the map did not exit, the player remained alive, kill count was zero, and reward was zero. It is not MAP01 completion, an independent model task-success score, a reliability estimate, or a matched token/latency/cost comparison. It uses the retained direct runner, not a model-connected standard public caller.

The packet is preserved byte-for-byte from the external scratch location; this audit is additive. The shared WSLc ownership issue #7924 remains STOP/HOLD. Do not infer that this past unique trial clears the shared allocation gate or authorize replay of R281. Any successor requires its own fresh allocation/attempt and current freeze.
