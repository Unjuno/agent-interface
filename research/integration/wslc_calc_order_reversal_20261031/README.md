# Calc grounding pilot: order-reversal replication

After the compiled-then-fresh pair in PR #9880, four new fresh allocations were prepared together and executed sequentially in fresh/compiled/fresh/compiled order. This reduces but does not eliminate order confounding; order was not randomized. Each new allocation uses identical runner, host, fixture and reference bytes to the previous pair. Main runtime base `38dafb8dde43b45811f959f73722ac0b9f6442d2` differs from that pair's base only by the previously recorded research evidence. Each process used `gpt-6.1-sol` low, private WSLc/Xvfb, the pinned Calc image, one CPU and no container network. Host model access remained enabled.

| Allocation | Route | Actual model calls | Input + output tokens | Task interval (s) |
| --- | --- | ---: | ---: | ---: |
| c06 (prior) | compiled | 1 | 12,279 | 7.559 |
| c07 (prior) | fresh | 2 | 24,542 | 12.775 |
| c08 | fresh | 2 | 24,542 | 11.559 |
| c09 | compiled | 1 | 12,263 | 7.799 |
| c10 | fresh | 2 | 24,542 | 26.300 |
| c11 | compiled | 1 | 12,279 | 8.827 |

All six saved the same cells and verified neutral input, per-operation release and owner-close release. Three compiled intervals have median 7.799 s (range 7.559–8.827); three fresh intervals have median 12.775 s (range 11.559–26.300). The long c10 interval is retained: its first recorded model-call envelope was 19.510 s. Per-run token totals use provider-reported input plus output; cached/reasoning subsets are not added twice. The extra fresh model call is intentional, and its result validates a reviewed point rather than controlling an autonomous planner. These three small fixed-task samples do not establish a confidence interval, service latency, fault equivalence, price, general speedup or performance on other apps.

The task interval runs on the container monotonic clock from before the first model request through session close and saved-file read/score, excluding startup, initial capture and final cleanup. Scripts and limitations are explained in PR #9880. `python audit.py` checks all six, including the earlier two archives, and fails if any required evidence or sample is missing. Four new archives preserve inputs, images, top-level outputs and model call results; nested protocol and owner journals are retained locally with their hashes and sizes. No sample was discarded or replaced.
