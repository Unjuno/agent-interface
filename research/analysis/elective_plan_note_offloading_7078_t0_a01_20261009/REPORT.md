# Issue #7078 T0 A01 result

**Disposition: `HOLD_AUDITOR_COVERAGE`.** The frozen candidate and auditor each ran once after freeze and both exited 0. The auditor returned PASS with no row-level errors: authored choices were NOTE for `beneficial`, NO_NOTE for `expensive`, and NO_NOTE for `unreliable`; all three rows carried `effect-17`. The output and stdout/stderr are retained under `results/`.

Post-run source review found a coverage gap: the auditor checked that the output retained the mandatory ID, but did not verify that the input ledger still typed that ID as `mandatory_unresolved_effect`. Therefore the preregistered mandatory-to-advisory input-role mutation was not actually rejected by this frozen audit contract. The PASS is preserved as the first result but is not promoted to `METHOD_PASS_SCOPED`.

Ten pre-freeze construction tests passed. Six semantic fault classes were represented, but mandatory-to-advisory laundering was only tested as output omission, not as role mutation at the input boundary. A02 is a separate successor allocation with an independently corrected auditor and explicit role-mutation control; it does not alter or replace A01.

The arithmetic is over hand-authored values only. No model q0 calibration, model or human continuation, actual storage/delivery cost, GUI behavior, or product benefit was tested.
