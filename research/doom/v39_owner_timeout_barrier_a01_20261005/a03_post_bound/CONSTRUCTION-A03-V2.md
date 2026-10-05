# A03 runner construction record — v2 deviation

The v2 runner completed both arms but did not implement the frozen 1.75 s gate delay. A text-replacement miss left `sync_open.set()` immediate in the timeout handler. The candidate accordingly stopped in 99,400 ns and drained an up row, which is not an observation of the A03 hypothesis. Its complete output is retained in `TOOL_STDOUT_A03_V2_CAPTURE.txt` and `results/a03_v2/RESULT.json`.

The pair is invalid for the frozen A03 decision and will not be relabeled. A v3 runner must verify before execution that the handler contains a 1.75 s timer and has no immediate gate-open call; then it may run the pair once into a fresh output directory.
