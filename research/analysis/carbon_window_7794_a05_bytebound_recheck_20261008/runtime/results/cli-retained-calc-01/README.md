# Primary CLI retention use in Calc

One fresh primary-agent WSL/Xvfb use of candidate `2bd4b652cb12aa4b86df719b59d191d8e1cc9760`, later integrated via [#3716](https://github.com/Unjuno/agent-interface/pull/3716). Each portable CLI observe/dispatch specified a new `--run-directory` and `--review --compact --report-refs`.

The primary viewed each screenshot, made an extra initial observation because startup drawing was incomplete, closed the visible tip, entered Quantity / Unit price / Total, 9 / 14 and formula `=B2*A2`, and saved. The action response still showed an intermediate/saving image. A read-only CLI review reproduced that exact historical image/outcome without changing attempt bytes or repeating input. A fresh observation then showed 126; saved FODS independently contains `of:=[.B2]*[.A2]` and numeric value 126.

Five attempts (observe, observe, dispatch, dispatch, observe) all retain request.json and report.json. Both dispatches completed with verified release. One additional review did not invoke a backend. This tests actual normal-path retention/recovery; no live stdout fault was induced. Broken stdout and write failures are separate construction tests in `runtime/cli_v1/test_attempt.py`.

## Inspect without rerunning

`evidence.tar.gz` contains 71 files: the original run records plus the exact candidate runtime, build manifest and checksum under `candidate/`. Every member is bound by `manifest.json`; `archive.json` binds the archive. The original local evidence digest manifest is retained unchanged. Run `python verify.py` with standard-library Python. It reads bytes directly from the archive and executes no archived program, model, input or application.

The verifier independently reads the saved formula/value, compares raw reports to CLI metadata, checks images and retained review equality, and checks recorded attempt counts and cleanup. It does not independently prove the live before/after file-immutability observation, primary image interpretation or process cleanup. Those remain scoped recorded evidence. Extract into a separate directory for manual screenshot inspection. Do not rerun the archived one-shot harness; its original local candidate path is preserved, while the candidate bytes are separately bundled for inspection.

## Outcome and limitations

Owner exited 0. Tracked Calc launcher/Openbox/Xvfb were reaped with 255/0/0; captured process-group member paths were absent. Full descendant closure is unverified; the retained lock file does not prove graceful application shutdown. No power-loss durability, forced live output loss, model usage, matched transport speed or formal Docker/OrbStack acceptance claim is made. CLI process timings include startup/persistence but exclude primary reasoning and host presentation; this run cannot isolate persistence overhead.

This evidence supports optional CLI retention and explicitly historical read-only recovery. It does not solve intermediate images or justify a longer default delay. Related: [#3711](https://github.com/Unjuno/agent-interface/issues/3711), [#3700](https://github.com/Unjuno/agent-interface/issues/3700). Earlier allocations remain unchanged.
