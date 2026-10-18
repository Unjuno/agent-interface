# Current-main paired-guard replay of a retained MAP01 threat trace

This posthoc replay addresses a narrow question: would the current V39 health/ammo pair monitor invalidate the same typed HUD sequence that produced one historical health-only cover invalidation during live MAP01 control?

## H / T / D / C / U

- **H:** With the exact retained source pair (sequence 166, health 61, ammo 40) and authored validity (critical health minimum 30; maximum health loss 10), current V39 admits a paired health/ammo monitor with hard health floor 51 and ammo floor 1. It should preserve the cover at equality and invalidate at the first later pair below either floor.
- **T:** Replay typed observations 167–218 from the retained `map01-v39-coast-liveness-live-01` event stream through the current-main `build_cover_monitor` and `DoomCoverSignalPairMonitor`. Independently scan event order, identity, freshness, thresholds, image hashes, and candidate output without importing the candidate or controller.
- **D:** A replay PASS requires all pairs to remain bound to increasing sequence/capture and the same surface; sequence 200 at (health 51, ammo 38) must preserve the policy; the first hard crossing at sequence 218 must be health 48 with ammo 37, require a new decision, and grant no input authority.
- **C:** The paired current monitor could behave differently because this source episode predates its paired-health/ammo implementation. Replay checks deterministic monitor classification on the recorded exact pair stream; it does not re-run the live event source or the controller lifecycle.
- **U:** One retained trajectory only. No current live input, cancellation/release path, independently useful feedback, bounded recovery, new task effect, survival comparison, MAP01 exit, reliability, or current-main live integration is established.

## Result

The candidate replay and independent raw-event auditor agree. All 52 post-source typed rows through sequence 218 were processed. Sequence 200 at health 51 and ammo 38 returned no invalidation; sequence 218 at health 48 and ammo 37 first invalidated with `health:below_hard_minimum`. Health was hard-invalidated, ammo remained a soft change, and the result required a new decision without granting input authority. The independent auditor verified exact paired epochs, increasing sequence and capture times, source binding, the 30-second age envelope, and decoded RGB hashes for source/boundary/trigger frames.

The historical report separately records an 8.916 s planner turn as interrupted, with the answer ineligible and discarded. Its guard-evaluation to interrupted-terminal-observation interval was 37.22 ms; this is cancellation closure timing, not a natural model-answer latency. The original live allocation used controller SHA-256 `cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e` at commit `5ffa6e0`, before the current paired monitor. The current controller SHA-256 is `f76c618f5eedbe2c301eecb67c36c9064ec0de035009d0be6f8610bb1d808dc8`.

This is a deterministic posthoc replay over retained live-run telemetry, not a new allocation or fresh current-main live exposure. The original episode ended after 50.371 s with one kill, zero deaths, and no MAP01 exit. The project’s live threat-control and task-completion gates remain open.

## Reproduction

From the repository root, use Python 3.12 with Pillow available:

```sh
PYTHONPATH=research/doom:research/live_control python3 research/doom/v39_current_main_paired_guard_replay_a01_20261005/replay_current_main_cover_guard.py --output /tmp/v39-paired-guard-replay.json
python3 research/doom/v39_current_main_paired_guard_replay_a01_20261005/audit_replay.py /tmp/v39-paired-guard-replay.json
```

The source and retained input identities are fixed in `SOURCE_LOCK.json`. The candidate refuses a mismatched worktree/source or an existing output path. The independent audit writes `AUDIT.json` in this directory. The referenced original run and raw event stream are not copied or edited.
