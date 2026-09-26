# Construction and formal stop record

All commands below were local Docker commands; no GitHub workflow was used to execute the experiment.

1. Construction smoke 1 stopped before session start: the read-only working directory prevented ViZDoom from creating `./_vizdoom/`.
2. Construction smoke 2 stopped before session start: `wmctrl` was absent from the image.
3. Formal v1 stopped at case `c03-drift-fresh-reanchor`: terminal state did not emit an additional interactive `observe` event.
4. Formal v2 stopped at case `c03-drift-fresh-reanchor`: the driver’s post/fresh indexing selected the same final observation and raised `IndexError`.

The image was rebuilt with `wmctrl`, and v3 changed the protocol so the bounded fresh observation is an explicit final `observe` step inside the submitted program. The failed allocations were not counted as PASS data and were not deleted.
