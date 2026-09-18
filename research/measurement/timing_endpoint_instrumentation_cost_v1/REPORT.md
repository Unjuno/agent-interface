# Complete typed timing instrumentation cost — first outcome

Decision: `PASS_TIMING_ENDPOINT_INSTRUMENTATION_COST_SCOPED`.

One source-first formal invocation; reruns0. Baseline and instrumented arms execute the same persistent planner-stub IPC, parse/validation, private state mutation/readback, independent effect score and terminal checksum. The only factor is constructing/serializing/validating seven typed #1176 endpoint records in the instrumented arm.

## 100,000 paired formal iterations

- baseline p50 **25.318 us**, p95 **37.366 us**, p99 **80.662 us**;
- instrumented p50 **46.770 us**, p95 **70.076 us**, p99 **123.376 us**;
- paired instrumentation delta p50 **20.070 us**, p95 **41.543 us**, p99 **94.062 us**;
- frozen PASS gates p50 <100 us and p95 <500 us both pass.

Every instrumented transaction supplied all seven RECORDED roles on one parent-process `perf_counter_ns` clock domain/epoch. All six #1176 intervals were reportable on **100,000/100,000** transactions. Gate failures0, independent effect failures0, terminal-verification failures0, authority/task-success promotions0. Serialized endpoint envelope is **1066 bytes** in every retained iteration.

Interval medians are descriptive harness timings only: planner_wait 22.624 us; response_to_accept 0.380 us; accept_to_input_ack 0.211 us; input_to_useful 0.361 us; observation_to_useful 0.201 us; useful_to_terminal 1.452 us. They are not frontier-model or GUI latency claims.

## Integrity

- RESULT SHA-256 `b6a9d06f22e209950c67962c5b1295911a89030b01aac7e4b6ecf72cff7ae2e1`;
- raw paired ledger gzip: 845,496 bytes, SHA-256 `fe8aac782c4e65b96b44bf2f4157644d4d0a52aca345b56687b5612e09bed9c3`;
- independent audit PASS/errors[];
- copied-result/raw-ledger corruptions5/5 rejected;
- postformal source rehash10/10 exact;
- formal invocation1/reruns0.

The full 845KB gzip timing ledger was consumed by the frozen auditor. GitHub publication retains its cryptographic commitment rather than transporting the binary through the text connector.

## Boundary

This closes only **local typed-envelope bookkeeping cost**. It does not measure the cost of obtaining authoritative endpoints from Calc/OpenTTD, a frontier model, X11 callbacks or independently useful real effects. The next #46 discriminator should charge event-source instrumentation in a real private application while preserving this exact typed admission contract.
