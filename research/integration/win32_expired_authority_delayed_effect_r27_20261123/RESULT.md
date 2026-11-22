# R27 — Three-attempt foreground-activated Win32 cohort

## Frozen design

R27 froze three independent attempts against main
`490d7bcb4d84927116112e5ff348cdeadfc489d6`. Each used one standard public
`focus + A + release_all` action, a 2 s lease, fixture text `a` scheduled 6 s
after key-down, and at most one fresh-session orphan recovery with a 2 s
late-input horizon. Before any MCP observation or dispatch, Computer Use
selected the unique owned fixture window by title, raised it, and an independent
probe had to match the exact HWND/PID. The full conditions and IDs are frozen in
`conditions.json`; all attempt receipts and screenshots are preserved in
`raw/`.

## Results

All three attempts passed the activation and foreground gate. Exactly one
public dispatch occurred in each; no dispatch was retried or replayed. The
source action was UNKNOWN, release-unconfirmed, task-success null and
replay-denied in all three. The independent fixture recorder observed the
expected factual text effect 6.000 or 6.016 s after accepted key-down, roughly
4.0 s after each 2 s lease boundary.

Each source MCP session was closed, the exact producer absence was verified,
and a new supervised session took a fresh no-input/no-authority observation
before exactly one orphan-recovery call for that source operation, target
generation and key obligation. All three recovery receipts returned
`recovered`, confirmed the A key-up, neutral readback and the 2 s late-input
horizon. Samples/gaps were 78 / 32 ms, 78 / 32 ms, and 77 / 32 ms (100 ms
maximum allowed sample gap). Every exact durable fence returned to `clear`, and
all three owned fixtures closed with their processes exited.

| Trial | Source action | Factual fixture effect | Recovery | Fence / cleanup |
|---|---|---|---|---|
| R27-01 | UNKNOWN; replay denied | `a`, 6.000 s after key-down | recovered; release + neutral + horizon verified | clear; closed |
| R27-02 | UNKNOWN; replay denied | `a`, 6.016 s after key-down | recovered; release + neutral + horizon verified | clear; closed |
| R27-03 | UNKNOWN; replay denied | `a`, 6.015 s after key-down | recovered; release + neutral + horizon verified | clear; closed |

The result is a 3/3 scoped reproduction under this single controlled fixture
and explicit activation protocol. It does not estimate general GUI reliability:
the trials share one host, fixture, workload and runtime, and all effects occur
after authority expiry. Factual fixture scoring is not eligible task success.
Recovery does not promote the UNKNOWN source action or permit replay. No model
or provider was used, so there is no efficiency, token, latency-comparison,
MAP01, Research Preview or distributable-runtime claim.

The runner, frozen IDs, all raw public requests/results, independent fixture
events/effects, activation records, fence snapshots and cleanup receipts are
retained in this packet. `raw/cohort-summary.json` reports
`PASS_SCOPED_THREE_ATTEMPT_COHORT`; that label is limited to the stated
mechanics, not a reliability pass for the product.
