# Plan — native X11 pacing mechanism CPU cost v1

Question: at the retained requested 1.0 ms strict-lowercase-ASCII pacing target, can a lower-CPU pacing mechanism preserve the same durable Calc correctness and control gates as the precise busy-wait implementation?

Read-only dependency source is the frozen native tight text path from source freeze `48030f5829690bdd3209d05974e390d88e7742a9` plus the precise busy-wait transformation already retained by sub-ms robustness v2. Common semantics, corpus, admission, stale rejection, release logic, target acquisition and scorer are unchanged.

Mechanisms are fixed before formal execution:
- `busy`: full monotonic busy-wait for requested 1.0 ms after each character;
- `sleep`: Go `time.Sleep(1.0 ms)` after each character;
- `hybrid200`: deadline-based pacing, `Sleep(remaining - 200 us)` then busy-wait the final tail when positive.

The controller records process user+system CPU time with `getrusage(RUSAGE_SELF)` around the edit Execute call only. The same interval retains wall time and measured character-start intervals.

Formal schedule: 6 fresh sessions per mechanism (18 total), six three-session batches using two Latin-square cycles:
1. busy, sleep, hybrid200
2. sleep, hybrid200, busy
3. hybrid200, busy, sleep
4. busy, sleep, hybrid200
5. sleep, hybrid200, busy
6. hybrid200, busy, sleep

Every session uses fresh private Xvfb/Openbox/LibreOffice Calc/XLSX and the same 16-string corpus. Independent post-execution workbook scoring is required. Stale observation must inject zero input and terminal release must verify empty. Semantic failure does not abort a batch. No formal reruns.

Mechanism correctness eligibility requires 6/6 exact durable sessions and all controls. `LOWER_CPU_EQUIVALENT_CORRECTNESS` requires at least one eligible non-busy mechanism with median edit process CPU <= 50% of the eligible busy reference. Report CPU/wall/interval tradeoffs separately; no automatic product-default promotion.

No model/provider/network calls. This does not measure whole-agent latency, energy, power, WSLg/Wayland/Windows/macOS, Unicode/IME, or scheduler generality.
