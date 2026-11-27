# R35 preparation and custody

R35 uses a fresh one-shot standard-caller attempt on current main, with R34b frozen as predecessor. Preflight binds the source commit, all packet source hashes, predecessor raw/supplemental audit/posthoc trace hashes, read-only registry state, and instrumentation self-test before input.

The central diagnostic is a pre-armed independent process that samples same-generation Q state every 10 ms from before dispatch, avoiding post-event process-start latency. The first injected Q-up callback is held 700 ms after cancellation. Immediately before cancel, the probe computes elapsed callback age plus planned hold and sends cancel only if the projection is at most 950 ms. If not, it releases the callback and records a pre-cancel stop. No registry setting is changed.

This sub-second run is diagnostic only. The R29 gate remains a separate 1250 ms condition; no result here can be described as a strict-gate PASS. One fixture, one dispatch, at most one cancel, no retry/replay, no text input, bounded cleanup, foreground restoration. Runtime task_success stays null.
