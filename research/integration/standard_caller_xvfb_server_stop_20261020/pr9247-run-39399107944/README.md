# Current-main Xvfb stop and fresh-target recovery — run 39399107944

This is a fresh retained Linux CI run of the #9247 private-Xvfb test, after the
final test fixes at source head `8fb84c6fcfca4b617eb22fe708e6d3fb9b3e1f40`.
That source is an ancestor of current main. The untouched workflow artifact is
[`standard-mcp-xvfb-server-stop.json`](standard-mcp-xvfb-server-stop.json);
its SHA-256 is in [`SHA256SUMS`](SHA256SUMS).

## Conditions and result

- GitHub Actions [run 39399107944](https://github.com/Unjuno/agent-interface/actions/runs/39399107944), Runtime X11 v1 Integration, completed successfully. Test source blob: `f38d77f55440d7918d6e85c61bfbd3e907854ccb`; workflow blob: `7a55cdd03b0a21f595860d8ba9166b4863008106`.
- The run owns private Xvfb `:88`. It holds key `a`, commits synthetic app effect `[1]`, then stops the exact Xvfb process. Cancellation returns in `0.409 s` before server resume and retires the owner, but XRes disconnect times out; release is `not_attempted`, `release_confirmed=false`, cleanup `UNKNOWN`, runtime `task_success=null`, and replay denied.
- The independent parent X client reads key `a` still down at the declared task horizon. The first task oracle correctly returns `fail` / `task_success=false`. Post-resume `interface_close` later verifies key-up, but the close receipt remains cleanup-failed/UNKNOWN and cannot upgrade the expired task.
- A separate bounded recovery task starts a new caller and window. The old alias is refused before input; fresh observation and mint create a new target generation; exactly one new `b` press produces effect `[0]` to `[2]`. Independent readback confirms both keys up at release and at the horizon. The separate recovery oracle passes in `527.051 ms`; runtime `task_success` stays null.
- Final test cleanup confirms both keys up. This is one synthetic Xvfb pass, not physical-input evidence, an outage-time release bound, a general X11 reliability rate, MAP01 transfer, provider/model integration, or efficiency evidence. No WSLc/Docker allocation was used.

The failed outage-era task and successful post-resume recovery are separate outcomes. The pass does not erase the held-key horizon failure or convert cancellation into verified release.
