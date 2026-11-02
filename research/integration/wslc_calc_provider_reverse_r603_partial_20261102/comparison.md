# Descriptive comparison of completed Calc provider cells

These are five individual observations, not a benchmark result or a causal estimate. The first order was direct → compiled → fresh; the reverse order was fresh → compiled → direct, interrupted by the Docker Desktop restart before direct. The table preserves that missing observation. All five used the same staged 171 source/input/driver hashes, synthetic task and requested model. Each row is one sample.

| Block | Route | Model turns | Task seconds | Host seconds | Input tokens | Cached input subset | Output tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| first | direct | 2 | 11.047 | 17.281 | 25,716 | 12,160 | 140 |
| first | compiled | 2 | 10.818 | 16.813 | 25,723 | 12,160 | 140 |
| first | fresh | 3 | 13.349 | 19.390 | 40,602 | 25,600 | 186 |
| reverse | fresh | 3 | 15.356 | 21.516 | 40,646 | 21,504 | 202 |
| reverse | compiled | 2 | 10.712 | 14.125 | 25,714 | 20,352 | 124 |
| reverse | direct | — | — | — | — | — | — |

Task and host intervals have different boundaries; host time includes setup and executable hashing. Cached input is already included in input. Fresh requires three turns in this experiment, versus two for the other routes; provider/cache conditions vary and reverse fresh had zero cached tokens on its second turn. Do not interpret differences as a speedup or reliability estimate. All completed cells passed their scoped effect, release and cleanup checks; compiled required a fresh-cue recovery after SAFE_YIELD. See each cell’s observations and audit artifacts for scope and limits. A later direct cell after Docker restart would include an environment intervention and must not be presented as an uninterrupted block.
