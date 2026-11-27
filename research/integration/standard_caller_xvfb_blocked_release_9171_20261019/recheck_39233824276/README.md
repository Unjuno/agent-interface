# Standard MCP Xvfb blocked-release recheck — run 39233824276

This is an additive record for GitHub Actions run [39233824276](https://github.com/Unjuno/agent-interface/actions/runs/39233824276), PR [#9171](https://github.com/Unjuno/agent-interface/pull/9171), after its branch was updated to include the then-current main. The earlier first outcome in the parent directory remains unchanged.

## Frozen run identity and scope

- Event: `pull_request`; PR head SHA: `202dc596b90850a5e6d978715ec7c5e0a307e951`; base SHA: `dfaf003a021611aab4f3f6082938794c61f645aa`.
- The raw artifact's `source_identity.github_sha` is `f217182827d2010c34c688ed9c91b0032d932b9e`; preserve it as reported by the runner, distinct from the PR head SHA.
- Test: standard MCP caller; private X.Org Xvfb; real python-xlib `Display.sync` blocked on an injected delayed request; synthetic application and synthetic input. This is a CI-host integration run, not WSLc, a physical desktop, or a product task.
- Xvfb identity recorded in raw: `/usr/bin/Xvfb`, package `2:21.1.12-1ubuntu1.8`, SHA-256 `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`.
- Run result: `FAIL`; the retained JSON, observation PNG, run metadata, and X11 integration log are copied without editing. `SHA256SUMS` covers these raw files.

## Result

The app's synthetic held `a` was observed down before cancellation. Cancel returned in 1,319.1 ms. The owner process retired by SIGTERM and PID-qualified XRes observation reported its client disconnected in about 60.5 ms. However, the release worker itself hit its 250 ms supervision timeout and was retired by SIGTERM before returning a release receipt. The caller therefore reported `owner_release_attempt.status=unknown`, `release_confirmed=false`, `cleanup_status=UNKNOWN`, and `task_success=null`. `late_server_request_possible=true`.

The test also failed because the worker's readback remained `unknown` rather than `readback_verified`. This is meaningful evidence that process retirement and X-client disconnect do not establish that a request already blocked inside the server was released or that the key is up. The XRes observer succeeds; the held-input release remains unproved. The test harness cleanup is not evidence of a runtime release result.

## Disposition

Preserve this as a second, distinct failed outcome after the process-kill escalation change. Do not overwrite or reinterpret the earlier run. Do not claim bounded release, task success, finite application recovery, or WSLc/MAP01 qualification from this result. Next code investigation should trace why the release worker cannot finish while another client is blocked in `Display.sync`, and define a bounded UNKNOWN path that does not require the blocked owner connection to answer. Any new formal test run must have its own run ID and retained first outcome.
