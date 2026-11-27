# Native WSL Xvfb target-generation and recovery integration — r03

Run ID: `native-wsl-xvfb-generation-recovery-r03-20261020`  
Source commit: `108b2717289611b4be84b897b2c56ef14a3f6032`  
Test blob: `31cba573f41fef7b9ca77921a742e00cfea1b3d1`

## Result

The standard MCP caller's live-Xvfb generation/recovery integration test passed once (`PASS_SCOPED_XVFB_STANDARD_CALLER_RECOVERY`). The exact raw report is `result.json`; the initial observation image is `result.observation.png`; `audit_raw.py` independently checks the saved predicates and emits `audit.json`.

The caller observed process and window generations as 64-hex values, admitted one initial action, then exercised the injected input/release fault. Recovery completed in **33.033 ms** with release verified. An independent X client read the recovery key up. The caller required a review, returned `task_success=null`, and denied replay. A pre-recovery alias was refused before dispatch. After new observation/rebinding, the continuation changed an independently read application property from `[2]` to `[3]`; its input produced a key press and key release, with **36.326 ms** from call start to effect commit. Runtime `task_success` remained null; the observed property/key sequence is the scoped synthetic task oracle, not a product-level result.

A destroyed/replaced target's old generation was refused with `input_dispatched=false`; the target-query worker was retired and review remained required. Final close independently verified both key and button sets empty. The private Xvfb process was stopped and its recorded PID was absent after the run.

## Frozen conditions and environment

`CONDITIONS.json` and `run.sh` were stored before the test. One test invocation used native Ubuntu 24.04.3 WSL, Python 3.12.3, python-xlib 0.33, Pillow 10.2.0, NumPy 1.26.4, MCP 1.30.0, and Xvfb `2:21.1.12-1ubuntu1.8` (the previous CI runner used `1ubuntu1.9`). `environment.txt`, `pip-freeze.txt` as included in it, `xvfb.log`, `stdout.txt`, `exit-code.txt`, and `xvfb-after-run.txt` preserve the run conditions and raw result. The temp venv is placed in the WSL distro home so a distro stop cannot erase it between setup and test.

Two earlier attempts stopped before Xvfb launch and are retained as separate prelaunch STOPs in `local-native-wsl-generation-r01/` and `local-native-wsl-generation-r02/`. They are not test outcomes and were not retried under those run IDs.

## Scope

This validates one synthetic standard-caller target-generation, recovery, stale-refusal, and effect path on native WSL Xvfb. It is not WSLc portability, physical desktop input, MAP01, full-X-server-stop release, a population reliability estimate, or matched efficiency. It creates no caller-level task-success claim. No WSLc container, Docker, model, game, or external GUI was used; no WSLc/MAP01 allocation was consumed or renewed.
