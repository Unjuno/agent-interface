# Construction record — Issue #4462

This source freezes paired balanced control versus a stratified treatment. Both arms share initialization and minibatch indices. Only 1,024 CORRECT training rows differ: 512 from band A and 512 from band B. Construction tests do not call training or formal.py; they validate data shape, band bounds, seed disjointness, gate logic and fixed controls. Formal evidence is not yet present.

Formal source and independent auditor will run once together in the cached local CPU Docker image with no network and dedicated output. Formal STOP/failure output is retained; no retry.

Pre-freeze construction caught two harness issues before any optimizer call: the first negative gate fixture changed only one of 1,024 CORRECT proposals, which correctly remained above the 0.95 recall threshold, so it did not exercise a failing gate; the fixture now corrupts 100 rows. A separate `py_compile` attempt tried writing `__pycache__` into the read-only source mount and failed with `EROFS`; it performed no training. Use Python's `-B` test invocation instead. Both are construction-only failures and are preserved here.
