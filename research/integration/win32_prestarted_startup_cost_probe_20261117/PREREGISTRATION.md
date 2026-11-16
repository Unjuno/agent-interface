# Win32 producer startup-cost probe (2026-11-17)

## Question

Does prestarting the native one-use producer reduce producer startup cost, or
move the same cost from per-action admission to server initialization?

## Scope and method

- Source: PR #10350 head `8846fa3fd67c6b74a50cdcfa3589ca82071e0daa`.
- Host: this Windows host; record Python version and OS build at execution.
- Five paired repetitions, alternating order: ordinary producer, prestarted
  producer, then prestarted, ordinary, and so on.
- Ordinary measurement starts before `Process.start()` after factory/action
  construction and ends when `Process.start()` returns. Factory construction
  time is separately recorded.
- Prestarted measurement starts before factory construction and ends after the
  ready receipt is received. This includes server-side producer preparation.
- Both routes use the actual `NativeWin32StandardProducerFactory`, one inert
  fixture HWND value, and one operation descriptor. The authorization gate is
  never opened; no native input or GUI action is sent.
- Preserve every trial, order, phase duration, environment and cleanup result.
  Report medians and paired differences. Five pairs are descriptive only.

## Interpretation limits

This isolates parent/child startup and readiness, not target binding, model
reasoning, application work, recovery, or full interface efficiency. Moving a
delay to before task admission is not by itself a total lifecycle speedup.
No production or MAP01 outcome will be inferred.
