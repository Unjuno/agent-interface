# Portable zipapp public MCP on X11 — smoke experiment

## H/T/D/C/U

- **Hypothesis:** The committed portable runtime zipapp can expose its optional stdio MCP interface outside a repository checkout and complete one bounded X11 fixture action while returning image content separately from JSON metadata.
- **Minimum discriminator:** From an unrelated temporary working directory with no repository `PYTHONPATH`, initialize MCP stdio, discover exactly `interface_observe` and `interface_dispatch`, observe the explicit Tk fixture, dispatch once to type/save a unique marker, then verify the saved marker independently and verify the retained cleanup receipt.
- **Decision rule:** Pass only if the portable process starts, both MCP tools are discoverable, each call returns exactly one image block, the independent effect file contains the exact marker, retained reports exist for both calls, and cleanup reports verified release. Any missing condition is a failure; no efficiency or model-facing usability inference follows from a pass.
- **Competing explanation:** A source checkout import path, a stale X11 server, action replay, or a success inferred only from the API receipt could falsely suggest package usability. The server ran from a temporary cwd with repository `PYTHONPATH` omitted; target ID came from the independently started fixture; the harness issues one dispatch only and checks the fixture's file output separately.
- **Uncertainty:** One deterministic fixture run establishes only this package/dependency/display combination. It does not test host MCP configuration, real application variation, host image presentation, model-visible feedback, delayed/stale image handling, or performance. Docker Desktop was unavailable, so this was WSL/Xvfb rather than a container run.

## Recorded run

- Date: 2026-09-20 (Asia/Tokyo).
- Source revision pinned into the archive: `52260e2c7f296771db3c9e725bbd0a427a4b014f` (current main at final run).
- Artifact: 149,849 bytes; SHA-256 `b8809721d8465963a59ac74484835b98846b308e43e31a97e4a919f3a8019d52`.
- Runtime: Python 3.12.3; optional MCP SDK 1.30.0; WSL Ubuntu; Xvfb display `:92`.
- Result: pass for the discriminator. Both tools discovered; explicit initial observation and the one dispatch each returned one MCP image block; two retained reports existed; dispatch completed and `release_verified=true`; independent `effect.json` was `{"saved":true,"text":"portable-mcp-01"}`.
- The dispatch used a fixed 100 ms `wait_update`; this is not redraw acknowledgement. No replay, model/provider call, host-presentation timing, or model-visible latency/token measurement was performed.
- Regression checks: `python -m unittest runtime.distribution_v2.test_distribution` passed 6/6 on Windows; `python -m unittest runtime.cli_v1.test_mcp_server runtime.selector_v1.test_selector` passed 23/23 on WSL Python 3.12.3 with `mcp==1.30.0`.
- Docker Desktop was not used. The installed Desktop CLI's `docker desktop start` returned “Docker Desktop is already running”, but `docker desktop status` and `docker --context desktop-linux version` then remained unresponsive until interrupted; the Windows `com.docker.service` was stopped/Manual. No container execution is claimed. Initial harness attempts exposed WSL's `/tmp/.X11-unix` mount as read-only with mode 0777: its server created an abstract X socket, so filesystem-socket polling was the wrong readiness condition. An early post-action harness assertion also read the cleanup receipt at the wrong nesting level; the saved fixture effect, returned image and execution had succeeded, but the harness marked the run failed until that evidence path was corrected. The final harness probes the selected display with `xdpyinfo` and reads the retained receipt correctly. These were harness/setup failures, not runtime failure evidence.

## Reproduction

Build the zipapp from the repository root using Windows Python (the WSL view of this Windows worktree cannot resolve its `.git` file):

```powershell
python -m runtime.distribution_v2.build `
  --out $env:TEMP/agent-interface-runtime.pyz `
  --manifest $env:TEMP/agent-interface-manifest.json `
  --sums $env:TEMP/agent-interface-sha256.txt
```

Start a private Xvfb display, install the optional SDK and X11 dependencies in a Python 3.12 environment, then invoke `run_smoke.py` with the archive, fixture, interpreter, selected display, and a result path. The server itself runs with a temporary cwd and a clean environment that does not include repository `PYTHONPATH`. Do not use an occupied or user desktop display for this fixture.

`result.json` is the machine-readable summary from the successful run. The harness uses temporary fixture, request, report, and image directories and removes them on exit; it stores no user screenshots or host-specific absolute paths in this record.
