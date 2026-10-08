# Active-turn observation delivery against the installed Codex App Server — A02 / A04

## Result

`PASS_SAME_TURN_OBSERVATION_QUEUED_AFTER_CURRENT_INFERENCE` for one bounded loopback-only mock-provider probe against installed `codex-cli 0.160.0` (`codex.exe` SHA-256 `37762753b554982eef1c109303d1be652b6397f1479e844794353a85650199c6`). The probe sent the `turn/start` + `toolOutput` shape used by V39 observation-delivery PR #7965 while the initial mock Responses call was held open.

The steering request returned the original turn ID. After the first response was released, App Server made a second Responses request for the same turn, and that request contained both observation text and a valid PNG data URL. It did **not** start the follow-up request before the original inference response completed. The first response remained pending for 1.516 seconds after `toolOutput` was sent; the follow-up request began immediately after release (0.000 ms at retained timestamp precision). Both mock API requests went to the local loopback server, the turn completed, the App Server process exited 0, and no game, model provider, GUI, or OS input was used.

The `turn/start` parameter shape is documented by the [official App Server `TurnStartParams` schema](https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/schema/typescript/v2/TurnStartParams.ts). The checked-out project source was not modified.

## H/T/D/C/U

- **H:** Active-turn `toolOutput` carrying a fresh observation interrupts or restarts current model inference, or otherwise causes another model request before the first response completes.
- **T:** Start installed App Server with an isolated `CODEX_HOME` pointing at a loopback mock Responses API. Hold response 1 open; send a `turn/start` with empty `input` and the PR #7965 `toolOutput` structure; record same-turn response identity, request ordering, and whether the follow-up request contains text and image. Release response 1 after 1.5 s if the follow-up request has not begun. No retries or external provider calls.
- **D:** PASS for active-turn context delivery if steering retains the original turn ID and the follow-up model request contains text and image. PASS for in-flight interruption only if that request starts before response 1 completes. This probe passed context delivery and failed the in-flight interruption criterion.
- **C:** This establishes App Server 0.160.0 behavior with a deterministic mock provider. It does not prove model comprehension, a changed answer, reduced end-to-end latency, useful game feedback, controller action changes, or a live MAP01 outcome. A different App Server build or provider could behave differently.
- **U:** Does planner follow-up on the integrated current-main controller change a pending decision usefully, and is the extra sequential inference worth its added latency/tokens? Does a live HUD event cross the authored guard and yield earlier per-key release/recovery under threat? Those remain unmeasured; the latter requires an authorized live-game lane.

## Reproduction and retained follow-up

`run.py` is the exact A02 script retained with the first outcome. `run_portable.py` is the corrected portable runner. A03 is retained as a harness failure: the release event was set before the first request, so steering arrived after the initial turn had finished and returned a different turn ID. Its process receipt was 0, but its result failed the same-turn condition; its Python runner then returned 1 because Windows still held the temporary Codex home open during cleanup. Do not treat A03 as a reproduction.

A04 is the corrected replay using a fresh output directory. The app-server process and runner both exited 0; the independent receipt auditor passed all eight checks, including mutation controls. Its second request began 16 ms after the held first response completed. This reproduces the queued follow-up behavior while allowing normal scheduling delay.

From Windows PowerShell with Python 3.11 and Codex CLI 0.160.0:

```powershell
python .\run_portable.py --out-dir .\results\a04-reproduction
python .\audit_result.py .\results\a04-reproduction
```

The replay uses a local loopback HTTP server, a fresh isolated `CODEX_HOME` naming only `127.0.0.1`, and a valid generated 2×2 RGB PNG. Each run writes receipts to its required fresh output directory; `process_exit.txt` retains the App Server exit code and `result.json` retains the structured observation. Scratch homes are preserved because Windows may keep runtime files open after process exit; they are outside the evidence package.

App Server 0.160.0 created local state databases and managed skill copies in that isolated home. Those generated runtime files are excluded from the evidence package; `.gitignore` excludes both `codex-home/` and `cwd/`.

The evidence branch was fast-forwarded from `ea2af10f1111ba614311e354dfecde1bbf653981` to current `main` `f59b2494f403b33349cbf202b49d76caef3d6d82` before files were added. The intervening main commit was unrelated; this package adds non-runtime research evidence only.

## Scope and disposition

This is App Server transport construction evidence only. A02 and the corrected A04 support the conclusion that active-turn delivery is queued for a follow-up inference rather than interrupting the currently pending inference in the tested App Server. It may affect the eventual turn answer, but does not show reaction before the slow inference returns or reduced waiting. Keep the #59 live threat-exposure/per-key-release/useful-feedback/recovery/progress/terminal gate open. No runtime or controller source was modified by this probe.

