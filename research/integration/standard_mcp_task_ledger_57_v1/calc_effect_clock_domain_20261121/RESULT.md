# Calc effect clock-domain repair — 2026-11-21

## Finding

On Windows CPython 3.11.9, the registered Calc profile and its task artifact use `time.monotonic_ns`, while `runtime/guarded_x11_v1/compiled.py` supplied `time.perf_counter_ns` to the compiled graph. These clocks are monotonic but their epochs differ on this host. The pre-fix diagnostic recorded the request inside the `persist_document` verifier callback, yet it was 21,510,700 ns before `effect_verification_started_ns` in normal mode and 34,489,700 ns before it under `-O`. Acceptance was after the request in both runs. The interval check therefore compared unrelated clock domains.

The registered Calc owner now supplies `profile.clock` as the effect-verification clock. The receipt names that domain as `time.monotonic_ns`. Graph observation, admission, execution, cancellation and method-deadline timing remain on the existing `perf_counter_ns` graph clock. Generic routes continue to use their graph clock for effect timing. The deadline is checked with the graph clock before reading the effect clock.

The core regression deliberately uses disjoint graph/effect clock values, places a request inside the verifier callback, and asserts `started < request < accepted`. The deadline regression calibrates against the graph clock while supplying an independent effect clock.

## Verification

Base: merge-main `338e2e8ac17cdccbe2fbe24d739a955134b9702c`. Source ran on Windows CPython 3.11.9 and in the pinned `agent-interface-xvfb-mcp:late-input-r19` image (`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`). Docker used no network, 2 CPUs, 4 GiB memory, 256 PID limit, read-only source and a separate evidence mount.

| Gate | Windows normal / `-O` | Pinned Docker normal / `-O` |
| --- | ---: | ---: |
| Core compiled GUI suite | 36/36 / 36/36 | — |
| Calc artifact suite | 20/20 / 20/20 | — |
| Provider-to-public-MCP composed Calc path | 1/1 / 1/1 | 1/1 / 1/1 |
| Registered Calc owner and partial-cancellation boundary cases | — | 9/9 / 9/9 |

The final Windows composition runs took 28.048 s normal and 22.462 s under `-O`. The final Docker composition runs took 10.352 s and 10.585 s. The separate Docker owner/cancellation group took 25.530 s and 24.526 s. All final raw logs are under `raw/final-*`.

The two pre-fix clock traces and two earlier diagnostic failures are retained under `raw/pre-fix`; only the two trace runs contribute to the reported clock-offset observation. An initial post-change composition invocation used a relative `PYTHONPATH` after changing directories and failed to import `runtime`; it was corrected to absolute paths before the recorded pass. An early deadline-test calibration also assumed the effect and graph clocks shared reads; the fixture was corrected to isolate the graph clock. Neither attempt is counted as a passing run.

## Scope

This repairs and verifies the synthetic Fake X Calc composition on Windows and pinned Linux Docker. It does not establish live provider use, live GUI task success, MAP01, broad recovery reliability, integrated efficiency, Research Preview acceptance or distribution readiness. Issue #57 remains open.
