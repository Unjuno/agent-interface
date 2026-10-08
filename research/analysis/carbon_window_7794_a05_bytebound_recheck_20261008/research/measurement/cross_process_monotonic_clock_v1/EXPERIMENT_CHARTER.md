# CROSS-PROCESS-MONOTONIC-CLOCK-COMPARABILITY-20260917-001

H: Same-host CPython subprocesses share one monotonic axis for `perf_counter_ns()` and `monotonic_ns()`, so child receive/send timestamps lie within the causal parent send/receive bracket for every valid exchange.

T: 32 fresh sequential child subprocesses × 4096 ping-pong exchanges = 131,072 rows. Standard library only. One construction invocation. Retain raw gzip transcript, summary, audit, environment metadata and source hashes. Fixed corruptions: nonce mismatch, duplicate seq, reversed child tuple, parent receive-before-send, synthetic +1s child offset.

D: PASS only if all real rows satisfy containment for perf and monotonic clocks, exact accounting holds, clock metadata is monotonic/positive-resolution, and all fixed corruptions are rejected by independent audit.

C: Causal containment shows a common comparable axis on this host but not exact event timing; IPC/scheduler latency widens brackets. Different hosts/VM clocks remain out of scope.

U: Linux/CPython/current container only; no X11, application callback, MAP01 or hard-real-time claim.
