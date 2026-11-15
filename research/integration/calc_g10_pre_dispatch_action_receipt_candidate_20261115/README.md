# G10 pre-dispatch action receipt candidate — 2026-11-15

Base `origin/main`: `f0d5fa202de83f39012bf4a914369b21f8e98a41`; candidate HEAD before this change: `a457d54bb3ea43edd39422ae887099a5002880c5`.

## Change and scope

`runtime/guarded_x11_v1/compiled.py` exposes an optional trusted-caller `before_action_dispatch` hook. After fresh admission, the actual bridge invokes it only when input-guard verification succeeds. The adapter supplies its own action name, minted action ID, operation, last observed process/window generations, and `time.perf_counter_ns()` timestamp immediately before guarded input dispatch. Public graph input cannot choose this callback. The existing post-release callback remains the source of transition acceptance and release evidence.

The G10 offline composition now joins the pre-dispatch record to the completed transition by exact action ID and checks timestamp ordering. The saved FODS payloads and X11 bridge remain fixtures. This does not implement a public G10 profile and does not establish live Calc, OCR/reference grounding, native GUI effect, or #57 efficiency.

## Verification

Python 3.11.9, Windows host. Commands:

- `python -m unittest runtime.guarded_x11_v1.test_compiled runtime.guarded_x11_v1.test_calc_g10_action_custody_composition runtime.guarded_x11_v1.test_calc_g10_artifact_v1` — 68/68 passed.
- `python -O -m unittest runtime.guarded_x11_v1.test_compiled runtime.guarded_x11_v1.test_calc_g10_action_custody_composition runtime.guarded_x11_v1.test_calc_g10_artifact_v1` — 68/68 passed.
- `git -c core.whitespace=cr-at-eol diff origin/main..HEAD --check` — passed; the retained raw test logs use Windows CRLF line endings.

Raw output: `normal.log`, `optimized.log` in this directory.

## SHA-256

- `normal.log`: `7465b3272eb7dc08a65e78f0b185cd63bc87cc80ef1b70e7b35eecefa82016f5`
- `optimized.log`: `4182d513e1066700573de77a948ff623412f2d68114e3cf64037af8942e903da`
- `runtime/guarded_x11_v1/compiled.py`: `a2e194148b3b5f184af1ba30f01c29e0fbda0ed5d3468eb7721ddefed11fbce3`
- `runtime/guarded_x11_v1/test_compiled.py`: `e28439ac055871b1c2adb819fa201536d85d907972d1926733457b8684acd0f0`
- `runtime/guarded_x11_v1/test_calc_g10_action_custody_composition.py`: `c911ce9420a05b3933ada1f1b0cd2694bfc7b431da5ffb27f8c5444f32892d69`

Candidate-only; no push or main modification.
