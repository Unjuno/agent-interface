# MAP01 OS rolling history v3 — retained partial failure

**Decision: `ABORT_PAIR_FRESHNESS_PRIORITY`.**

Three of sixteen frozen cases completed. The explicit 50–100 ms temporal binding interval eliminated v2's out-of-contract 35.9 ms pair. However, the frozen ranking minimized distance to the 70 ms target before considering recency. In closing/history case 2 it selected indices 51/53 from the retained ring because their gap was closest to target, even though fresher admissible pairs existed. Controller-start observation age was **613.138 ms**, so the unchanged 500 ms freshness gate correctly yielded with zero task input.

The allocation is stopped and not pooled or completed. V4 changes one thing only: within the admissible temporal interval, rank by newest current capture first and only then by gap error.
