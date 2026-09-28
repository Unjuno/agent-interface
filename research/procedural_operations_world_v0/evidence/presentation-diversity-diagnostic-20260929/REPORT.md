# Presentation-family diversity diagnostic (2026-09-29)

Disposition: `PASS_PRESENTATION_DIVERSITY_DIAGNOSTIC_ONLY`.

This is exploratory construction evidence for Issue #5206, not a preregistered
formal benchmark allocation, agent/controller score, evidence of anti-
specialization, or promotion result. No benchmark defect was established.

## H / T / D / C / U

**H.** The existing sparse-render hash check may overlook same-seed
presentation-family framebuffer collisions because it samples one pixel in
every 97; full-frame rendered variation over requested family keys could
detect a collision missed by that sparse check.

**T.** Current-main source at `1314d8d0113fcef1b72694e6ca0431b5420f74c5`.
WSL2 Arch Linux, GCC 16.1.1. Existing `make clean all && make test` plus a
120-frame headless smoke. A separate diagnostic renders 256 seeds x 20
requested family keys (5,120 combinations), forces the target cue visible,
records 64-bit FNV-1a over all 640x360 pixels, and compares distinct actual
presentation families within each seed. For requested sample seed 234, it also compares the
existing stride-97 pixel hash across all 190 family pairs. No agent acts and no
score is read.

**D.** Construction succeeds only if warning-enabled build and existing
validity tests pass, all 12 generated presentation families appear, no
same-seed distinct-presentation full-frame hash collisions occur, and the sampled
stride hash has no duplicate pair for sample seed 234. A failure would be a
diagnostic hold requiring classification—not a scored-agent failure. The
initial Windows `make clean` invocation failure and the first diagnostic
helper's impossible sample-seed guard are retained as tooling defects; the
corrected helper is not used to erase or reinterpret those failures.

**C.** Fixed source and configuration, deterministic seeds 0..255 and
requested family keys 0..19; frame hashes are compared only within a seed.
This is host-local WSL execution, not Docker, GPU, model/provider, GUI/X11,
input dispatch, or a scored episode.

**U.** Hash uniqueness does not prove visual-semantic diversity, resistance to
generator specialization, held-out family transfer, evaluator isolation, or
formal benchmark validity. Requested keys 2 and 11 collide at seed 57 because
both map to actual generated presentation family 2; this is ordinary finite
family-key mapping, not two different rendered layouts colliding. The full
frame hash is only a diversity sentinel, not a perceptual or semantic metric.

## Result

- Warning-enabled native `make clean all`: exit 0, no compiler warnings.
- Existing validity suite: `20/20 validity-hardening tests PASS`.
- Headless run: seed 20260929, family key 88001, 120 frames, 2.0 simulated
  seconds; report `done=false`, `success=false`, `failure=none`, zero actions.
  This is a renderer smoke, not task performance.
- Diagnostic: 5,120 combinations, generated-family mask `0xfff`, cue-mode
  mask `0xf`, zero full-frame collisions across distinct actual presentation
  families, and one requested-key alias: seed 57, keys 2/11, both actual
  family 2. Sample seed 234 had 20/20 distinct full-frame hashes and 0/190
  stride-97 hash collisions.
- No plausible renderer defect was detected. The issue remains open with its
  formal-benchmark HOLD.

## Preserved execution/tooling failures

1. A Windows-host `make clean all` failed before compilation because GNU make
   attempted to execute Unix `rm`. No source/output was touched by that failed
   command. The same intended construction commands were then run once under
   WSL; this environment failure is not treated as benchmark evidence.
2. The first audit-helper draft checked `seed == 2026` inside a loop bounded
   to seeds 0..255, so its sample-only comparison never ran. Its output was
   invalid for that comparison and is not used. The helper was corrected to
   explicit sample seed 234 before the reported diagnostic run.
3. An intermediate helper revision incremented the sampled-pair denominator
   twice. Its displayed 0/380 was invalid and is not used. The retained final
   helper counts each unordered pair once; its result is 0/190.
4. WSL `/tmp` outputs were transient and absent in a later WSL invocation.
   Exact PPM/JSON hashes from the first smoke were printed at execution time,
   but the byte files could not be retained or independently rehashed later.
   This limits the smoke's evidentiary strength; no rerun was made.

## Frozen source identities

Main commit: `1314d8d0113fcef1b72694e6ca0431b5420f74c5`.

Git blob IDs: `test_ops_world.c` `f369fb7b76db2b7761ae431598133aa39571e0fa`;
`ops_world_part_00.inc` `9bf195cebd4de73e348af071091a49fb4a835f64`;
`ops_world_part_01.inc` `118db3d10fbb20e28cce61eda231bea47173dbcd`;
`ops_world_part_02.inc` `8e3396329ada48a1e49a11d952b4d96798dc5e0b`;
`ops_world_part_03.inc` `5a29fedbe547dfbd9c255866e21f91f3f92bf078`;
`ops_world.h` `1f37ced44340d1d54b8a49e83e9a0d2fd1743a4f`.

The tested source bundle is not modified. The standalone diagnostic helper is
retained beside this report. Temporary build products and smoke outputs remain
outside tracked evidence.
