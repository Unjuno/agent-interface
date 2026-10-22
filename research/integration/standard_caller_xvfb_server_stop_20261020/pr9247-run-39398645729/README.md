# PR #9247 private-Xvfb server-stop and fresh-target run

- GitHub Actions run: https://github.com/Unjuno/agent-interface/actions/runs/39398645729
- Linux job: `x11-integration`, succeeded.
- Tested code head: `3912d156405ede9cb9ff72dbd7fdeaef2b6398ab`.
- Scope: owned standard MCP caller, private workflow-owned Xvfb stop/resume, and a synthetic application. The original outage task and the later recovery task are scored separately.
- Raw artifacts: server-stop artifact `12252768041`; blocked-release artifact `12254315117`.

## Original outage task

The cancel returned `cancel_unconfirmed` while Xvfb was stopped. No release was attempted during the outage. After resume and at the observation horizon, an independent reader still saw key `a` down, so the original task's independent oracle failed. A later explicit close read both keys up; that later cleanup does not revise the original task outcome. Runtime `task_success` stayed null.

## Fresh-target recovery task

A distinct post-resume task passed in 540.578 ms. It used a new window (`2097154`, previous `2097152`) and a fresh process generation. The old alias resolved to terminal `refused` without dispatch. Fresh observation and mint succeeded, followed by one new `b` press. A separate reader verified application effect `[0]` to `[2]`, both keys up after release and at the horizon, and exactly one `b` press. The independent synthetic recovery oracle passed. Runtime `task_success` stayed null; this pass belongs to the test's independent oracle, not the runtime receipt.

## Blocked-owner companion result

The blocked-owner artifact records `owner_release_attempt=readback_verified`, a passing synthetic task oracle, and no delayed press. The overall cancellation remains unconfirmed, cleanup remains `UNKNOWN`, `release_confirmed=false`, replay remains disabled, and runtime `task_success` remains null. Keep this uncertainty separate from the fresh-target recovery pass.

## Integrity

- `standard-mcp-xvfb-server-stop.json` SHA-256: `fb830d3bed290381305b41b07469cb20abdd812603a49aabd8e05574efeb92af`
- `standard-mcp-xvfb-blocked-release.json` SHA-256: `f3dfa4a8cf46134ecb9d6a19c223b7f79d4003899a8a13915ba359607772bf80`
- `standard-mcp-xvfb-blocked-release.observation.png` SHA-256: `751e00d5f926a15128a45baec1b2310aabee740b363119bd79dd224986d81f01`

These results are limited to private-Xvfb synthetic scenarios. They do not establish physical-input release, release while the X server is stopped, MAP01 success, WSLc behavior, cross-platform reliability, or efficiency.
