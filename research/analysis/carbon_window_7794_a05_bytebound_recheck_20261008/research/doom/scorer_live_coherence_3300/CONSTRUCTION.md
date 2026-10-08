# #3300 live ViZDoom scorer coherence — construction record

Status: `HOLD_LIVE_SPAN_UNIDENTIFIED` (construction only; no formal allocation)

## H/T/D/C/U

- H: The real ViZDoom 35 Hz API boundary can be instrumented to retain episode-tic brackets, individual API call spans, and inter-attempt timing without changing the existing three-attempt coherence policy.
- T: Use an isolated Docker container, pin `vizdoom==1.2.3`, load the bundled `basic.wad` MAP01 fixture, configure 35 Hz and hidden PLAYER mode, and collect eight consecutive two-read brackets around `get_episode_time()` with one tic advancement between samples.
- D: Retain the exact container recipe, package version, fixture path, per-call monotonic spans, episode-time values, coherence labels, and all setup failures. This is a construction probe, not the preregistered phase/load-stratified formal allocation.
- C: Construction PASS requires the pinned package/import, fixture initialization, 35 Hz configuration, and complete raw bracket rows. Formal #3300 PASS additionally requires frozen phase/load strata, three-attempt traces, independent audit, and SHA-256 manifest.
- U: No private MAP01 allocation, no controlled load strata, no scorer integration, no model/GUI/input, and no efficacy or gameplay claim.

## Obstac construction results

1. `--network none` dependency-isolation attempt:
   `STOP_SETUP_OR_INFRA`: pip could not resolve `vizdoom==1.2.3` without a preloaded wheel. This was a dependency acquisition stop, not a scientific failure.
2. Network-enabled dependency acquisition and execution:
   `OBSTAC_VIZDOOM_IMPORT PASS version=1.2.3`
   `OBSTAC_VIZDOOM_35HZ_SPAN_PROBE PASS samples=8 coherent=8`
   Fixture: bundled `basic.wad`, MAP01, hidden PLAYER, 35 Hz.
   Bracket spans (ns): `[5876,2875,1583,1458,2500,1542,1459,1250]`.
   Episode pairs: `[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8)]`.

The first run exposed and preserved a path-join construction error (`scenarios_path+"basic.wad"`); the successful probe uses `os.path.join` and does not alter production scorer code.

## Formal next gate

Freeze the current-main scorer source, ViZDoom/WAD identity, phase offsets, idle/fixed-load/delayed-read strata, and three-attempt trace schema. Then run exactly one episode-disjoint allocation. Until those are retained and independently audited, the live-coherence result remains HOLD and must not be promoted from construction PASS.
