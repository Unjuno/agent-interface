# Construction-clock-31 — stdout ordering stop

Disposition: `STOP_LOG_ORDER_UNBRACKETED`; no scientific conclusion.

The first diagnostic enabled ViZDoom `viz_debug 2` and printed parent-side
passive-window markers, but stdout was block-buffered. Child `VIZ_Tic` lines
were interleaved with parent markers (including a split line), so log order
could not establish which internal tic events fell inside the measured window.
The raw API snapshots, scorer calls and cleanup remain retained in `raw.json`;
they do not answer live engine progress. Do not count the visible tic numbers
outside a validated bracket or pool this run with construction-clock-32.

This harness stop was corrected by line-buffering child stdout with `stdbuf
-oL` in the separate construction-clock-32 run. The initial log and raw SHA-256
are recorded in `invocation.txt`; no files from this run were overwritten.
