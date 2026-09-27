# LibreOffice controller-lock boundary v1

## Result

`CONTROLLER_LOCK_NOT_SEMANTIC_EXCLUSION_SCOPED`.

Fresh LibreOffice Draw 25.2.3.2 document/process per case, ten first measured cases under the frozen schedule.

- `locked_stable`: 5/5 controller observes A=1000, holds `XModel.lockControllers()`, writes A=1200; B remains 5000.
- `locked_intervening_write`: 5/5 independent UNO subprocess connects while `hasControllersLocked()==true`, changes A 1000->1700, and still sees the lock true after the mutation. The controller then performs the frozen stale write to A=1200 before unlocking; B remains 5000.
- Independent audit passes all 10 cases and verifies event ordering `lock_verified < external_write_complete < stale_write < unlock`, lock-state evidence, final geometry, schedule, and frozen source hashes.

## Interpretation

For this real Draw/UNO boundary, `XModel.lockControllers()` does not exclude another UNO client from mutating document object state. It therefore cannot turn a separate read/validate then `setPosition` into a target-state compare-and-mutate operation. The result is consistent with the public UNO contract, where `lockControllers()` suspends controller/display-update notifications rather than documenting object-write mutual exclusion.

This result falsifies only this candidate lock mechanism. It does not test `XUndoManager.lock`, a cooperative in-process macro/extension, crash atomicity, authorization, or other LibreOffice object/property semantics.

## Evidence boundary

GitHub retains frozen source/preregistration/schedule/environment, complete compact per-case event/result records, independent audit, and manifest. The local complete evidence archive additionally contains per-case soffice stdout/stderr and raw runner ledger.
