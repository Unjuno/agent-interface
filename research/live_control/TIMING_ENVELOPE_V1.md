# Process-scoped end-to-end timing envelope

Issue #46 asks the project to stop mixing local runtime time, model time, file or
adapter delay and planner absence. `timing_envelope_v1.py` records ordered events
with an explicit state, process-scoped monotonic clock, uncertainty, cause and
details. `OBSERVED` requires an integer timestamp and clock domain. `MISSING` and
`NOT_RECORDED` require null time and clock fields. Intervals across a missing
endpoint, different domain or reversed order return no duration.

Six malformed-record controls refuse. Same-process, missing and different-domain
interval controls pass. A process clock does not claim comparability with the
model subprocess, Linux runtime or OS clocks. Timing metadata grants no action
authority.

## Fresh Calc episode

A new seed-238 Calc session used the existing typed Luna/low supervisor and saved
A1=480 and A2=192. Two model actions entered both cells/Save and handled the
format dialog; a third model decision requested independent verification. The
XLSX values and runtime task score pass. The audit replays 63 events, 12 exact
frames, 17 durable append records and 10 socket exchanges. There was one Save.

The Windows supervisor records 22 timing events on one `QueryPerformanceCounter`
domain. Its defined first useful feedback endpoint is detection of a file that
contains both a fresh observation and typed terminal. File polling contributes
at most the declared 25 ms endpoint uncertainty.

| Interval | Measurement |
| --- | ---: |
| Initial observation detected → semantic completion detected | 23,975.674 ms ±50 ms endpoint bound |
| Model request → proposal, turn 1 | 7,446.120 ms |
| Proposal published → first useful feedback, turn 1 | 1,104.917 ms ±25 ms |
| Useful feedback → next planner request, turn 1 | 7.888 ms |
| Model request → proposal, turn 2 | 5,986.394 ms |
| Proposal published → first useful feedback, turn 2 | 872.903 ms ±25 ms |
| Useful feedback → next planner request, turn 2 | 6.638 ms |
| Total wrapper-observed model wait over three turns | 21,334.161 ms |

The wrapper-observed model waits occupy about 89.0% of the measured initial-
observation-to-completion interval. This identifies the dominant measured share
in this episode; it is not a population estimate or a claim that model inference
alone caused all wrapper time. Provider request receipt/first token, runtime
receipt and OS injection remain explicitly `NOT_RECORDED`. Linux runtime timings
stay in their original domain and are reported separately rather than converted.

The previous automatic Calc episode took 32.570 seconds from Linux initial
capture to evaluation and used four model turns, while this one took 23.494
seconds and three turns. Prompts, caches, model outputs and episodes differ, so
that descriptive difference is not a speedup comparison.

## Instrumentation overhead failure and v2

V1 flushes and `fsync`s every event. Isolated 200-record measurements found
5,263.7 us median on Windows and 8,701.632 us on Linux. That design is rejected
for the critical path. The live Calc result remains valid evidence with this
instrumentation included, but must not be used to claim uninstrumented latency.

`timing_envelope_v2.py` buffers records and performs one explicit durability sync
at close. In separate 200-record runs, record medians fell to 18.1 us on Windows
and 14.718 us on Linux; p95 was 46.9 and 17.49 us. The one close-time sync took
3.517 and 8.797 ms. These runs compare different durability semantics and are not
randomized application-overhead trials. V2 can lose buffered timing records if
the recorder process dies before close. It is the candidate for the OpenTTD
integration, not a default runtime promotion.

Primary evidence:

- `results/timing-envelope-calc-01/audit.json`
- `results/timing-envelope-calc-control-01/timing-envelope.jsonl`
- `results/timing-envelope-controls-01/`
- `results/timing-envelope-cost-windows-01/`
- `results/timing-envelope-cost-linux-01/`
- `results/timing-envelope-v2-cost-windows-01/`
- `results/timing-envelope-v2-cost-linux-01/`
- `results/timing-envelope-cost-audit-01.json`

The next domain envelope is now recorded in
[OpenTTD adaptive live control](TIMING_ENVELOPE_OPENTTD_V1.md). One fresh v8 run
passes the independent four-part road guard in 111.853s using two Luna-low then
six Astra-medium calls. Wrapper-observed model wait is 91.781s. Earlier
OpenTTD failures remain preserved. This is an adaptive candidate, not a matched
speed comparison; do not infer cross-domain timings.

Next run matched fixed-Luna, fixed-Astra and adaptive allocations on the same
OpenTTD task, followed by the corresponding Calc strategy comparison.
