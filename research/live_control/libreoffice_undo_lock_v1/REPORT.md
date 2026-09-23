# LibreOffice undo-manager lock boundary v1

## Result

`UNDO_MANAGER_LOCK_NOT_SEMANTIC_EXCLUSION_SCOPED`.

Fresh LibreOffice Draw 25.2.3.2 document/process per case, ten first measured cases under the frozen schedule.

- `undo_locked_stable`: 5/5 controller observes A=1000, holds `XUndoManager.lock()`, writes A=1200; B remains 5000.
- `undo_locked_intervening_write`: 5/5 independent UNO subprocess connects while the shared undo manager reports `isLocked()==true`, changes A 1000->1700, and still sees the undo manager locked after mutation. The controller then performs the frozen stale write to A=1200 before `unlock()`; B remains 5000.
- Independent audit passes all 10 cases and verifies event ordering `undo_lock_verified < external_write_complete < stale_write < undo_unlock`, lock-state evidence, final geometry, schedule, and frozen source hashes.

## Interpretation

For this real Draw/UNO boundary, `XUndoManager.lock()` does not exclude another UNO client from mutating document object state. It therefore cannot make a separate read/validate then `setPosition` operation atomic. The result is consistent with the API role of `XUndoManager` as the undo/redo manager; locking it does not establish a document object compare-and-mutate boundary.

This result falsifies only this candidate lock mechanism. It does not test a cooperative in-process macro/extension, custom document transaction, crash atomicity, authorization, or other LibreOffice object/property semantics.

## Evidence boundary

GitHub retains frozen source/preregistration/schedule/environment, compact measured evidence, independent audit and report. The complete local evidence archive additionally contains per-case soffice stdout/stderr and raw runner ledger.
