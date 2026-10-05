# Issue #7741 T0b — candidate runtime STOP

## H/T/D/C/U

**H.** Lower interaction cost (10→6) can increase task starts and peer adoption enough to raise population p95 latency on a shared one-server verifier versus frozen adoption; the reversal should be absent under no imitation, nonbinding capacity, or per-principal partitioning.

**T.** `FREEZE.json` declares 24 principals, ring/star networks, 160 ticks, four seeds, imitation 0.08/0.2, route start probabilities 0.12/0.22, service time 3, matched keyed opportunity draws and the event audit. No model, GUI, live service, GPU, or user data.

**D.** A valid disposition required complete candidate output plus an independent raw event replay and all frozen negative controls. Candidate runtime exception is `STOP_CANDIDATE_RUNTIME`; no hypothesis verdict is available.

**C.** Adoption can be independent of interface cost; bounded task starts or nonbinding/partitioned verification can eliminate the mechanism.

**U.** All adoption and queue parameters are synthetic and uncalibrated; no real-world effect transfers.

## Execution

The first candidate invocation exited 1 before emitting JSON (captured stdout file is 0 bytes). Observed traceback: `candidate.py`, `simulate`, line 73, `TypeError: string indices must be integers, not 'str'`, at `job["finish"]` while iterating shared-mode `busy` as though it were a list of queue lists. The auditor was not invoked. There is no scientific result.

The invocation did not capture a pre-run source hash or a separate stderr receipt, and the working candidate was subsequently edited while diagnosing the exception. Therefore this is explicitly a provenance-incomplete construction STOP, not an auditable formal candidate run. Do not label the edited source as the exact invoked source or retry it under T0b. A fresh version must hash its candidate before execution and capture stdout, stderr and exit status separately.
