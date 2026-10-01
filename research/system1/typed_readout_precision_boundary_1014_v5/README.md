# Issue #4912 — selected-code precision construction v5

Fresh successor allocation after the preserved v4 host STOP. V4 did not create a container or load the model, so no row was evaluated. This distinct one-shot allocation uses the same preregistered excluded rows and numerical gates; it does not alter or retry v4.

The frozen PowerShell wrapper `invoke_construction.ps1` verifies source/corpus/model hashes, pinned image, empty raw output, one-shot marker and (at launch) idle GPU. `-PreflightOnly` checks the command without starting Docker; the only launch mode is explicit `-RunConstruction`. The wrapper issues `docker run` and stores stdout/stderr/receipt in a sibling logs directory outside `/out`.

Rows: B00/B17/B63 × suffix slots 0/7/15; answer-token IDs 15–22; FP16/BF16/FP32. No formal timing rows, generation, training, semantic scoring, GUI or authority change. The exact paths, commands, source hashes and thresholds are in `FREEZE.json`.