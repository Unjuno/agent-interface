# T0 result

Disposition: `PASS_METHOD_SCOPED`; 5 protocols, 15 model images, 0 candidate/auditor discrepancies, and 0 retry-authorized states. The independent auditor rejected a mutation that labeled an effect-only state `NO_EFFECT_CONFIRMED` and enabled retry.

The separated-store models include effect-only and receipt-only durable images, both classified `UNKNOWN_RECONCILE`. The atomic-transaction model contains only neither/both images under its declared abstraction. These outcomes establish only what follows from the chosen finite model. No host/storage stack was exercised; machine-crash T1 remains untested and requires a separately validated isolated VM/harness.
