# Frozen natural-threat attempt on the persistent v26 controller

`map01-persistent-threat-v26-live-02` used the unchanged v26 controller for one
preregistered 12-decision Luna-low run at seed 990619.  V23 had reached visible
enemies at this seed, but this run authored a different route and stalled around
the first AGM door.  The exact decision-frame contact sheet shows no visible
enemy; manually transcribed health remains 100 and ammunition 50 in all twelve
frames.  The independent score is alive and unfinished with zero kills, deaths,
or exit after 66.636 seconds.

The allocation is therefore retained as
`RETAINED_NATURAL_THREAT_AND_INVALIDATION_UNEXPOSED`.  It does not test the
natural planner-interrupt path.  Natural policy invalidations, planner
interrupts, cover renewals, and model-authored nonempty covers are all zero.
The normal path remains internally consistent: one app-server process spans
three four-turn threads, all twelve typed turns complete, all 29 admitted cover
and plan programs verify empty release, and zero MCP startup notifications are
present.

Cumulative per-turn usage reconciles to 117,225 input tokens, including 77,184
cached input tokens, plus 1,717 output and 560 reasoning tokens.  Model wall time
is 53.864 seconds.  These values describe this unexposed allocation and do not
support a gameplay or token-efficiency comparison.

The result changes the benchmark design.  Seed alone does not reproduce a
threat state when model-authored navigation differs.  Repeating MAP01 from the
spawn point would mostly resample navigation and add little evidence about
stale-cover invalidation.  ViZDoom's official `DoomGame.save` and
`DoomGame.load` APIs preserve and restore engine state; the documentation also
states that loading does not reset the episode tic counter or reward state:
<https://vizdoom.farama.org/main/api/python/doom_game/>.  The next construction
should create a hash-bound Freedoom MAP01 checkpoint through recorded OS-input
setup, load it before measured control begins, and retain an exact initial frame
showing a real enemy.  Custom scenarios are useful but would answer a different
question from real MAP01.

Run the retained audit with:

```sh
python research/doom/audit_map01_persistent_threat_v26_live_v2.py
```

This result makes no causal survival, reliability, generality, human-speed,
Product Hunt completion, or MAP01-clear claim.
