# #59 — scorer overrun and command-service construction A01

This is a deterministic boundary experiment, not a live allocation or a change
to the deployed session. Both `sources/retained/` files are exact main bytes;
`sources/fair/` contains the two minimal proposed command-probe changes.

Worker: `01a0ff52-e0cc-7e81-b3ed-36b1d84d7a9a`; FINAL-v5. Claim: #59 comment
5964226431. Dedicated branch: `research/59-scorer-fairness-01a0ff52`.

- **H:** Under sustained callback or sink duration at least one sampling period,
  the retained main-thread polling loop and stdin iterator can repeatedly sample
  without inspecting an already-ready finish command. Probing input after each
  completed sample avoids this particular starvation while keeping one owner
  thread and scorer data outside the command callback.
- **T:** Exact-source functions, inert ready-command adapter and injected integer
  clock. Two implementations × two source variants × nine literal cost scenarios
  = 36 rows. Costs are zero, half, one, two or ten periods, charged to the sample
  or sink separately. Eight completed samples bound the diagnostic; a ninth
  sample attempt terminates the assay. One candidate invocation and one separate
  raw-only auditor; no formal retries. Prior ordinary red/green regressions and
  fixture-layout import failure remain in `development/` and are not pooled.
- **D:** `COUNTEREXAMPLE_AND_REPAIR_CONSTRUCTION_PASS` requires all 12 retained
  sustained-overrun cases to exhaust the diagnostic budget without any input
  probe, all six retained fast cases and all 18 fair cases to deliver finish
  exactly once, same owner thread, exact command, complete raw coverage, and ten
  corrupted-raw controls rejected. Otherwise FAIL/HOLD with the first raw kept.
- **C:** The cost model is injected, not measured in ViZDoom. A sample that never
  returns blocks both variants. Command floods or long command handlers can
  delay scoring and are outside this ready-single-command assay. Callback errors
  are not converted into command delivery. No fabricated catch-up samples or
  scorer-derived command contents are allowed.
- **U:** No OS input, physical release, real game, model, container, live useful
  progress, measured wall latency, or scheduler reliability result. An eight-step
  trace alone is finite; the source recurrence below supplies the persistent-cost
  counterexample. Later runtime adoption needs separately reviewed integration.

## Source reasoning

In each retained loop, a due sample advances the next deadline past its starting
time and then unconditionally continues before the input check. With a returning
callback/sink cost of at least one period, the next deadline is due again on the
following iteration. Induction repeats this path without a readiness probe.
For exact period-multiple costs used here, the deadline advances to the next
period boundary and the callback returns at or beyond it. The fair copy falls
through to the ready-input probe (or buffered line) after the completed sample,
with a nonnegative wait timeout. It does not preempt an ongoing callback.

| 記号 | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| P | スコア取得の周期。固定値0.1秒 | s | 本構築試験のみ。実運用35 Hzの計測ではない | 正実数スカラー |
| C | 取得と保存の合計所要時間。時計に注入 | s | 0, 0.5P, P, 2P, 10P | 非負実数スカラー |
| B | 診断打切り前の完了取得数 | 1 | 8。安全期限や最大実遅延ではない | 正整数スカラー |

## Ordinary verification

`FAIRNESS_VARIANT=fair python3 -B -m unittest test_fairness -v` exercises the
original failing service condition. Existing polling, adapter and progress-clock
tests run with the fair copy and their unchanged source definitions. The first
export layout omitted the clock file loaded by an adjacent-path test: retain that
ImportError, then repair the export layout rather than changing the test/oracle.
