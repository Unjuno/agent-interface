# Golden desktop demo v1

The construction-phase entry point now runs the selected persistent Agent
Interface path with one command instead of requiring knowledge of the research
orchestration files. It preserves the frozen three-arm allocation unchanged.

```bash
./runtime/golden-demo.sh doctor
./runtime/golden-demo.sh audit-retained
./runtime/golden-demo.sh run
```

The current tested host is WSLg/Linux X11 with Google Chrome and the Windows
Codex CLI bridge. `doctor` checks every required path, Python module, X11
connection and CLI version before a model call or GUI session. Fresh runs use a
new `artifacts-local/` directory, refuse an existing output directory, and have
no automatic retry.

`setup-golden-demo.sh` was also exercised from a new `runtime/.venv`. It
installed the exact versions in `requirements-golden.txt` and the resulting
doctor passed every check. Chrome and Codex remain explicit host dependencies.

## Fresh retained run

`runtime/results/golden-desktop-live-02` is the first complete run through the
new entry point. Seed 991030 used Luna-low and returned:

| Metric | Result |
|---|---:|
| Independently exact submissions | 6 / 6 |
| Routes | cold, reuse, reuse, repair, reuse, reuse |
| Schema preflight + planner generations | 3 |
| Model-visible images | 2 |
| Actual input tokens | 26,531 |
| Cached input tokens, included above | 4,864 |
| Six-task elapsed time | 47.460 s |
| Whole command after doctor | 58.879 s |
| Input acknowledgement to next observation, median | 101.276 ms |
| Old-layout target pointer admissions | 0 |
| Verified terminal releases | 57 / 57 |

Task 4 first observed the old layout-A field handle as `MISSING`, issued zero
pointer input through that reference, made one repair grounding call on layout
B, and completed exactly once. Tasks 5 and 6 reused the replacement references.
`audit-live` recomputes the three unique model-call IDs and usage, exact append-
only submissions, raw missing-handle event, repair, and all terminal releases.

The earlier `golden-desktop-live-01` directory is retained as a construction
failure. Its fresh schema preflight completed, then the wrapper imported
`initialize` from the wrong module before GUI readiness. The fix moved the
correct import before process launch. No six-task or performance result is
claimed from that directory.

The first Windows video render also exposed WSL absolute image paths. The
renderer now rebinds each retained image basename to the supplied result root;
a following development invocation then exposed a missing `hashlib` import.
Both failures occurred before a published metadata file. The corrected renderer
produces `site/media/golden-desktop-live-02-2x-h264.mp4`.

The 26.75-second H.264 video is a labelled 2x timeline playback from 137 exact
retained observations across 47.472 seconds. When no new observation exists, it
holds the latest exact frame. It therefore does not invent intermediate motion
or claim to be an unbroken screen capture. The final card reports the fresh run,
and the landing page states this representation directly.

This new persistent-only run is a reproducibility and construction result. The
published 63,128/63,779/26,563-token and 56.412/73.238/44.131-second comparison
continues to come only from the earlier frozen three-arm allocation. Neither
result proves a population rate, broad GUI generality, production readiness or
human-level speed.
