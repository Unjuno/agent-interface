# PR #9247 private-Xvfb server-stop and fresh-target run

- GitHub Actions: https://github.com/Unjuno/agent-interface/actions/runs/39398645729 (Linux x11-integration succeeded)
- Tested head: 3912d156405ede9cb9ff72dbd7fdeaef2b6398ab
- Scope: owned standard MCP caller, private workflow-owned Xvfb stop/resume, synthetic application; the test has a separate outage-era task and a post-resume fresh-target task.
- Raw artifacts: server-stop ID 12252768041; blocked-release ID 12254315117.

## Server-stop and fresh recovery

The original outage task remains cancel_unconfirmed: release was not attempted during server stop, key  was still down after resume/horizon, and that task's independent synthetic oracle failed. The later explicit close read both keys up, but this does not change the outage task result.

A distinct recovery task then passed in 540.578 ms. It used a new window (2097154, previous 2097152) and a fresh process generation. The old alias reached terminal efused without dispatch; a new observation and mint succeeded; one new  action completed; an independent reader verified application effect [0] to [2], all keys up after action and at the horizon, and exactly one  press. The separate synthetic recovery oracle passed. The runtime's 	ask_success remains null. This is a test-defined task effect, not a runtime success claim.

## Blocked-owner companion result

The same run's blocked-owner artifact records owner_release_attempt=readback_verified and a passing synthetic task oracle with no delayed press observed. The overall cancel remains unconfirmed, cleanup remains UNKNOWN, elease_confirmed=false, replay remains disabled, and runtime 	ask_success remains null. Preserve the unresolved cancellation/cleanup state.

## Integrity

- standard-mcp-xvfb-server-stop.json SHA-256: $serverHash
- standard-mcp-xvfb-blocked-release.json SHA-256: $blockedHash
- standard-mcp-xvfb-blocked-release.observation.png SHA-256: $imageHash

These are private-Xvfb synthetic results only. They do not establish physical-input release, MAP01 success, WSLc behavior, cross-platform reliability, or efficiency.