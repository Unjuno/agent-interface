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

The exact A02 script is retained locally with the first outcome (SHA-256 `fa13b080b05c579c14f5422622449554a99b0819a460699cd75784623bdb6c6a`) but omitted from the public package because it embeds the local absolute workspace path. `run_a02_redacted.py` changes only that output-root expression. `run_portable.py` is the corrected portable runner. A03 is retained as a harness failure: the release event was set before the first request, so steering arrived after the initial turn had finished and returned a different turn ID. Its process receipt was 0, but its result failed the same-turn condition; its Python runner then returned 1 because Windows still held the temporary Codex home open during cleanup. Do not treat A03 as a reproduction.

A04 is the corrected replay using a fresh output directory. The app-server process and runner both exited 0; the independent receipt auditor passed all eight checks, including mutation controls. Its second request began 16 ms after the held first response completed. This reproduces the queued follow-up behavior while allowing normal scheduling delay.

From Windows PowerShell with Python 3.11 and Codex CLI 0.160.0:

```powershell
python .\run_portable.py --out-dir .\results\a04-reproduction
python .\audit_result.py .\results\a04-reproduction
```

The replay uses a local loopback HTTP server, a fresh isolated `CODEX_HOME` naming only `127.0.0.1`, and a valid generated 2×2 RGB PNG. Each run writes receipts to its required fresh output directory; `process_exit.txt` retains the App Server exit code and `result.json` retains the structured observation. Scratch homes are preserved because Windows may keep runtime files open after process exit; they are outside the evidence package.

App Server 0.160.0 created local state databases and managed skill copies in that isolated home. Those generated runtime files are excluded from the evidence package; `.gitignore` excludes both `codex-home/` and `cwd/`.

## Explicit-interrupt follow-up (A05/A06)

The A05 hypothesis and acceptance rule were fixed in [`PLAN_A05.md`](PLAN_A05.md) before the probe. A05 is a retained HOLD: App Server rejected its new turn because the top-level image input used `image_url`; the v2 `UserInput` schema expects `{ "type": "image", "url": ... }`. The first turn had already been interrupted, but the fresh-image turn was rejected, so A05 proves no behavior beyond that schema rejection. App Server exited 0; the runner exited 1. Its first audit is preserved in `results/a05-interrupt/audit.json`.

A06 applies that protocol correction under a separately fixed plan in [`PLAN_A06.md`](PLAN_A06.md). With the first mock response held open, `turn/interrupt` completed turn 1 as `interrupted`; a second `turn/start` on the same thread carrying fresh text and a valid PNG reached the loopback mock before the runner released response 1. Turn 2 completed, exactly two mock requests were made, and both App Server and runner exited 0. The current official [v2 `UserInput` schema](https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/schema/typescript/v2/UserInput.ts) encodes inline images with `type: "image"` and `url`.

The retained A06 clock readings tie at 1 ms host precision. Auditor v1 therefore failed its strict `<` timestamp check; its failure is retained as `audit_v1.json`. Auditor v2 accepts equality only when the recorded event barrier says the second request was observed before the first response was released; it also passes seven other ordering, content, exit, and mutation checks. This proves request ordering in this harness, not a latency distribution.

Reproduce A06 from Windows PowerShell with Python 3.11 and Codex CLI 0.160.0:

```powershell
python .\run_interrupt_probe_a06.py --out-dir .\results\a06-interrupt
python .\audit_interrupt_result_v2.py .\results\a06-interrupt
```

The evidence branch was fast-forwarded from `ea2af10f1111ba614311e354dfecde1bbf653981` to current `main` `f59b2494f403b33349cbf202b49d76caef3d6d82` before files were added. The intervening main commit was unrelated; this package adds non-runtime research evidence only.

## Scope and disposition

This is App Server transport construction evidence only. A02 and corrected A04 show that active-turn delivery is queued for a follow-up inference rather than interrupting the currently pending inference. A06 shows that explicitly interrupting the turn can admit a fresh observation-driven turn before the held response is released. That restart may discard useful work and requires another inference; no end-to-end latency, model decision quality, V39 interruption safety, live feedback, earlier per-key release, recovery, progress, or game outcome was measured. Keep the #59 live threat-exposure/per-key-release/useful-feedback/recovery/progress/terminal gate open. No runtime or controller source was modified by these probes.

