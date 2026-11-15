# G10 pre-dispatch action receipt candidate — 2026-11-15

Base `origin/main`: `f0d5fa202de83f39012bf4a914369b21f8e98a41`; candidate HEAD before this change: `a457d54bb3ea43edd39422ae887099a5002880c5`.

## Change and scope

`runtime/guarded_x11_v1/compiled.py` exposes an optional trusted-caller `before_action_dispatch` hook. After fresh admission and input-guard verification, the adapter supplies its own action name, minted action ID, operation, last observed process/window generations, and `time.perf_counter_ns()` timestamp immediately before the bridge interaction call. Public graph input cannot choose this callback. The existing post-release callback remains the source of transition acceptance and release evidence.

The G10 offline composition now joins the pre-dispatch record to the completed transition by exact action ID and checks timestamp ordering. The saved FODS payloads and X11 bridge remain fixtures. This does not implement a public G10 profile and does not establish live Calc, OCR/reference grounding, native GUI effect, or #57 efficiency.

## Verification

Python 3.11.9, Windows host. Commands:

- `python -m unittest runtime.guarded_x11_v1.test_compiled runtime.guarded_x11_v1.test_calc_g10_action_custody_composition runtime.guarded_x11_v1.test_calc_g10_artifact_v1` — 67/67 passed.
- `python -O -m unittest runtime.guarded_x11_v1.test_compiled runtime.guarded_x11_v1.test_calc_g10_action_custody_composition runtime.guarded_x11_v1.test_calc_g10_artifact_v1` — 67/67 passed.
- `git diff --check` — passed.

Raw output: `normal.log`, `optimized.log` in this directory.

## SHA-256

- `normal.log`: `97201d776a58297d7b06612cc7c6493a6f6c4cdedb53f24157cab2a491204614`
- `optimized.log`: `3ce00d213cbf9ccb27880e694b21cabea4ad6d5e61d6381ef603d705bd204c2b`
- `runtime/guarded_x11_v1/compiled.py`: `a3c141788fa1788772ff28408c57d819db85af8780ff825b096197bc1ea1c084`
- `runtime/guarded_x11_v1/test_compiled.py`: `f0a16f18be56af5b49bd3ea2947733eabdee0c4748675349471fe651520b69e0`
- `runtime/guarded_x11_v1/test_calc_g10_action_custody_composition.py`: `c911ce9420a05b3933ada1f1b0cd2694bfc7b431da5ffb27f8c5444f32892d69`

Candidate-only; no push or main modification.
