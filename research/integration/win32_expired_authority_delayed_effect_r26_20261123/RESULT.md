# R26 — Explicit foreground activation repeat

## Frozen scope

One independent trial was frozen against main `490d7bcb4d84927116112e5ff348cdeadfc489d6`. It retained the same Win32 fixture, one `focus + A + release_all` public action, 2 s authority lease, 6 s delayed effect, 2 s late-input horizon, and no model/provider. The setup change was to pause after fixture startup and require Computer Use to select the unique fixture window and raise it before the exact HWND/PID foreground probe and any MCP action. IDs and limits are in `conditions.json`.

## Result

The unique fixture window (HWND 3805226, PID 35208) was raised through Computer Use. The exact foreground probe then matched HWND, PID and title before observation/dispatch. One public dispatch occurred; no retry or task replay was sent.

The public action remained `UNKNOWN`, `input_dispatched=true`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`. The independent fixture record shows key-down accepted at monotonic `420902765000000` and text `a` at `420908781000000`, 6.016 s later and about 4.016 s after the 2 s lease boundary. Independent factual scoring is true, but the delayed post-authority effect is not eligible task success.

The source session closed with its action unresolved. A fresh supervised session verified the exact producer absent, obtained a no-input/no-authority observation, and made exactly one orphan-recovery call for the exact source operation/generation and key obligation. It returned `recovered`, with the A key-up confirmed, neutral readback, and 2 s horizon verified over 78 observations (32 ms maximum observed gap; 100 ms bound). The source action stayed UNKNOWN and replay denied; the durable fence became clear for the exact source operation/generation. The owned fixture was closed normally and process exit code 0 was recorded.

Full raw receipts, independent score, foreground activation and probes, source/recovery sessions, fence snapshots and fixture cleanup are under `raw/trial-01/`; the cohort ledger is `raw/cohort-progress.json`. This is one scoped repeat after the R25 setup failure. It does not establish reliability, provider/token/latency efficiency, MAP01, Research Preview graduation, or a distributable runtime.

## Interpretation

Explicitly raising the exact owned target addressed R25-02's pre-dispatch foreground mismatch in this single attempt. R26 reproduces the R24/R25-01 delayed-effect and one-shot-recovery boundary once. The three records support a finite next cohort only if setup activation is repeated and all attempts, including setup failures, remain in the denominator. The R25 failure remains separate and is not overwritten.
