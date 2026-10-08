# Issue #8636 T0 A02 — corrected focal-shift audit allocation

**Disposition: `HOLD_UNCERTAIN`.** The candidate completed 360 planned trials, but the single independent auditor invocation exited 1 at the status comparison gate before producing a summary. The exact first output and failure are preserved; no formal retry occurred.

A02 was based on current main and used new seeds 30030–30059 in each stratum. It separately predeclared a focal-shift `YIELD` as acceptable only when the independent auditor reproduced the frozen pairwise-shape gate failure and exact reason. It did not relax the 0.09-rad threshold or change the primary hypothesis. The auditor stopped at `ValueError: status does not match independent decision` (`auditor.py` line 280), but the retained traceback does not identify the first trial or row. Therefore this allocation establishes no feature-method or hypothesis result.

The candidate output was an exact 2,216-file / 63,085,782-byte tree, retained as `results/a02-first-outcome.tar.gz`. A temporary extraction was compared file-by-file to the original before removing the expanded duplicate; SHA-256 values matched. Exact candidate/auditor stdout, timestamps, exit codes, source and protocol freeze, and package checksums are retained. The independent audit has no summary artifact because it exited before writing one.

A01 remains `HOLD_UNCERTAIN` with its original first audit mismatch, source, and output unchanged. A02 is a separate consumed allocation and is not a replacement for A01. Any follow-up requires its own explicit hypothesis delta, fresh seed allocation, source freeze, and one-pass run.

No live GUI, game, OS input, model, human, task effect, physical release, runtime, product, or safety conclusion follows. The candidate and auditor were deterministic local CPU programs; no container or external service was involved.

Post-run custody review also found that `FREEZE.json` recorded Python 3.12.13 from the construction-test `python` executable, while the formal `python3` commands used Python 3.14.5. Because the protocol did not pin the resolved interpreter, environment equivalence is not established. This additional discrepancy is recorded without changing the first result or rerunning either formal program.
