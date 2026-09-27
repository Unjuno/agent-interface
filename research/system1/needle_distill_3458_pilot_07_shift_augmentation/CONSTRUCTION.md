# Construction record — Issue #3918

The source freezes paired balanced-control vs targeted-CORRECT-mixture training. Both arms share identical initialized weights and minibatch-index stream; only half of CORRECT training rows differ. Evaluation rows are generated once per seed and shared between arms. Construction tests must not call `train_arm`, `generate_result`, or `formal.py`; they validate data shape, mixture bounds, seed disjointness, gate calculation, and boundary/invalid counts only.

Formal source and independent auditor will run once together in the cached local CPU Docker image with no network and dedicated output. Formal STOP/failure output is retained; no retry.

Pre-freeze construction caught two harness issues before any optimizer call: the first negative gate fixture changed only one of 1,024 CORRECT proposals, which correctly remained above the 0.95 recall threshold, so it did not exercise a failing gate; the fixture now corrupts 100 rows. A separate `py_compile` attempt tried writing `__pycache__` into the read-only source mount and failed with `EROFS`; it performed no training. Use Python's `-B` test invocation instead. Both are construction-only failures and are preserved here.
