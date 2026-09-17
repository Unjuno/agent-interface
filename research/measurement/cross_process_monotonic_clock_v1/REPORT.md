# Same-host cross-process monotonic clock comparability — result

Issue: #1000  
Task: `CROSS-PROCESS-MONOTONIC-CLOCK-COMPARABILITY-20260917-001`  
BASE: `159dd3684ffcd0ee78b9ff5939e0173cd77c7b4f`  
Decision: **PASS_SAME_HOST_MONOTONIC_CLOCK_COMPARABILITY_SCOPED**

## H / T / D / C / U

The frozen hypothesis and test contract are retained in `EXPERIMENT_CHARTER.md`. One standard-library construction invocation launched 32 fresh child subprocesses sequentially with 4,096 ping-pong exchanges each (131,072 total). No X11, GUI, model/provider, task input, runtime mutation, or formal/live allocation occurred.

## First outcome

- rows: **131,072 / 131,072**
- missing / duplicate: **0 / 0**
- `perf_counter_ns` causal-containment failures: **0**
- `monotonic_ns` causal-containment failures: **0**
- direct `CLOCK_MONOTONIC` causal-containment failures: **0**
- all 32 child processes and the parent report `clock_gettime(CLOCK_MONOTONIC)`, monotonic=true, adjustable=false, nominal resolution 1 ns
- normalized child clock metadata (excluding PID): **1 unique shape**
- independent corruption controls rejected: nonce, duplicate sequence, child reversal, parent reversal, synthetic +1 s child offset — **5/5**

Descriptive scheduling/IPC values only: RTT p50 **32.159 us**, p95 **61.071 us**, p99 **111.105 us**, max **13.379 ms**. These are not performance gates or hard-real-time claims.

The local `perf_counter_ns - CLOCK_MONOTONIC` paired-call differences have median **-150 ns** and range **[-230974, -110] ns**; `monotonic_ns - CLOCK_MONOTONIC` median **-80 ns**, range **[-214239, -60] ns**. Negative signs are expected from call ordering and do not represent a process epoch offset.

## Interpretation

On this same Linux host / CPython build, raw `perf_counter_ns()` and `monotonic_ns()` values from separate processes behaved as one comparable monotonic axis under 131,072 causally bracketed exchanges. This supports direct temporal comparison of same-host input-owner and independent-scorer receipts **when both explicitly use this clock family**. It does not establish exact event time inside IPC brackets, cross-machine/VM comparability, wall-clock UTC comparability, or application callbacks using another clock.

## Integrity / first-outcome chronology

`run.py` completed successfully once and persisted the complete raw transcript and `result.json`. The enclosing ChatGPT container command later hit its 45-second limit while the subsequent audit was still running. The scientific runner was **not rerun**. `audit.py` was subsequently executed read-only against the retained first outcome and returned PASS.

The exact raw transcript is 10,603,284 compressed bytes and is **not Git-retained**. Its compressed SHA-256 is `fbd2d0bac930a5a5c4fa9517f50fd27248c14765dd981bd2506836fd630c9820` and uncompressed JSONL SHA-256 is `59f591738a9ea3f82f12fe63d72f4d2d55a4bd12a698b892a90bd393e4de3b1f`. `RESULT_PUBLIC.json` retains the scientific summary and provenance needed to distinguish this from raw retention.

## Limits / successor

This closes only the same-host clock-axis assumption. It does not close #998/#999 physical-edge instrumentation and does not establish application consumption. The next integration should require each scorer/input receipt to declare its clock source and may use raw timestamps directly only when the declared same-host monotonic-clock precondition holds.
