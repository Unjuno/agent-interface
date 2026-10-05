# A07 result — STOP before input treatment

A07 fixed A06's missing ExecutorV13 step field (`op: key_batch`) and ran one synthetic fake-X candidate against 21 files frozen from current main `9febfe4926cde6629f9751d6444f6b802cf31328`. The candidate command exited 0 and emitted both arms. In both arms, ExecutorV13 failed before any step completed with `ValueError('observed input focus required')`; `release_row` was absent and no key-release attempts occurred. Cleanup's final fake keymap was empty because the test never pressed a key.

Disposition: `STOP_BEFORE_TREATMENT_ACTION_FOCUS_ADMISSION`. This says nothing about dropped-KeyRelease recovery. The 18/30 auditor result is consistent with a pre-treatment STOP, not a treatment failure.

The first auditor process also stopped before raw checks because its package path was not mirrored at `/src/map01_v39_v15_perkey_cleanup_a07_20261005`. That packaging-only issue was corrected by exposing a byte-identical package copy at that path; the unchanged frozen auditor then completed once against the unchanged raw and returned 18/30. Candidate was not rerun. Both auditor attempts are retained.

No real X11, GUI, Doom, model, physical keyboard, application effect, formal allocation, or live-game evidence. WSLc: 3.0.1.0, Python 3.12.15, image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, network none, CPU 0.25, memory 512 MiB. The host emitted its swap-limit warning and `memory.swap.max` was `max`, so swap enforcement is not claimed.

Raw and audit: `results/candidate.json`, `results/audit.json`. See `FREEZE.json`, `PREFLIGHT.json`, and `RUN.json` for exact identities and execution facts.
