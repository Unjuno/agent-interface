# Iterator fallback and seeded-history Xvfb observations

This preserves follow-up evidence for the experimental segmented-history
candidate in [the earlier hybrid study](../wslc_idle_hybrid_history_20261101/).
It does not install the candidate in runtime. The baseline is draft PR #10074
at `0675ab810f7ee890d0904b8a402678c81f8dbafb`; main at freeze was
`504b013d81324b58b5d890d144b3b0d820cb3b3c`.

The previous segmented iterator differed from a dict when the mapping changed
size during iteration. The experimental repair materializes a dict on first
iteration. It passed 90 selected WSLc regression tests in both normal and
optimized Python. At 100,000 synthetic entries, median fork/insert/dispose
was 0.013–0.014 ms before iteration and 0.437–0.458 ms after iteration;
first iteration including conversion cost 2.161–2.271 ms. These are local
microbenchmarks, not task speed or a thread-safety proof.

In a separate private Xvfb trial, cancellation before publication and a publish
control both met their stated checks; the following fresh guarded session
produced a target `a` and verified key release. The instrumented mapping made
zero conversions on those paths. This does not cover other callers.

In four further serial Xvfb allocations (baseline/hybrid/hybrid/baseline),
each trial seeded 100,000 identical synthetic metadata entries and timed 21
real idle captures. Median capture times were 10.166, 9.168, 10.028, and
10.414 ms, respectively. Each allocation subsequently used a **fresh** owner
and history to produce and release `a` in an independent target. The action was
not timed and was not performed using the seeded history. The ranges overlap;
two trials per arm are insufficient to establish a general speedup. Old seeded
records have no valid artifacts and were not read. The limited result is not a
model, real-time guarantee, or MAP01 comparison.

`raw.zip` retains the four experiment directories, source, conditions, raw
outputs, prior failure, and follow-up audit. `archive-manifest.json` hashes
each included file; `python audit.py` verifies the archive and runs the saved
independent capture auditor in a temporary extraction. Host-specific
`private-command.json` files and Python bytecode are excluded; original local
copies remain intact. The Windows-only initial red-test traceback contains a
local path and is not published; its two tests and subsequent WSLc results are
included. See each directory's `RESULTS.md` for exact limitations and the
prior failed runner's UNKNOWN cleanup receipt. Audit success checks consistency
of evidence; it cannot independently establish past timing or absent events.
