# V15 cleanup-first CPython/WSLc recheck — frozen plan

## H/T/D/C/U

- **H:** The exact current-main + #8094 virtual-merge source tree preserves the cleanup-first per-key identity and finite handback behavior in its bounded synthetic regression suite under a pinned Linux CPython runtime.
- **T:** At most one ordinary run each (normal and optimized Python) of the seven scoped unit-module groups listed in RUN_PLAN.json, using exact virtual-merge tree 2ce07e058ed6b868ea97799e9a7b65deff21da71 from current main 2c1c90c80389dc6aab6a950c7058528272979f2d plus #8094 head a3132379705d10f2bbfd122de8dad7c0298c6e7b. Extract only the frozen top-level Python modules under research/live_control/ and research/doom/; no candidate/game/model execution.
- **D:** Each mode passes all 47 expected methods. Hard-change and UNKNOWN cleanup-first schedules must retain admitted key-up identity, discard the delayed answer, and allow the next planner turn only after a cancelled terminal with verified empty release. Persistent dropped-UP must remain failed/unverified, leave the synthetic key down, and prevent the next planner turn. No additional native/keymap query or authority is expected.
- **C:** Windows host, WSLc 3.0.1, Linux/amd64 image python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 (Python 3.12.15), one CPU, requested 512 MiB, no network, cached image only, read-only source mount, disposable container. The 512 MiB setting is not treated as proven enforcement; record any host cgroup/swap warning. This is synthetic fake-X/unit evidence, not native-X.
- **U:** A pass is cross-environment regression confirmation only. It does not establish threat detection, physical keyboard state, game/application consumption, useful live feedback, recovery efficacy, latency, gameplay outcome, or Issue #59 completion. The required fresh live threat exposure remains unallocated and unrun.

## First-outcome rule

Do not rerun either mode to turn a failure into a pass. Preserve each command, stdout, stderr, exit code, runtime/image identity, and any setup/cleanup STOP. Do not touch existing/stopped containers or images. No code repair or live-game action follows from this recheck alone.

## Reproduction

Run prepare_sources.py --manifest-only to write the pre-run frozen source manifest, then commit/push this plan, script, and manifest before candidate tests. Afterward materialize to a new external directory with prepare_sources.py --out <new-directory> --manifest <committed-manifest>; mount that directory read-only and run the exact commands in RUN_PLAN.json. Save raw outputs outside the source tree.
