# Explicit owned-service selection through V15/controller

Parent [#59](https://github.com/Unjuno/agent-interface/issues/59).
Base `7aeb6f933c67384ad0e8d3b25e1d68a44ec341a8`.
Reviewed composition `7323ac050272f94c1b220303c6eae60d151f407e`.
Original selection head `8a252071ea7fb5281b9ecc154fa1640136d5345c` is retained
as an ancestor through a normal historical merge whose tree equals its first
parent. The six original changed files are also preserved in `original-selection/`.
Older 149-method outputs are historical, not reused as current-main qualification.

## Selected behavior

Controller `--owned-input-service` requires `--measurement-session` and
`--target-process-identity`; `--target-window-lifecycle` is refused for this path.
Validation precedes planner/process startup. V15 validates before base import,
selects `session_owned_owner_backend.Backend`, strips wrapper flags before base
argparse and pins the additional selected sources. Defaults remain unchanged.

The wrapper launches one owned cancellation-enabled service and uses the actual
process-identity Backend/Executor adapter. Exclusive file-fsynced root receipts:

- `session-owner-service-startup.json`: accepted child startup plus owned PID.
- `session-owner-service-startup-failure.json`: retained handle/cleanup diagnostic;
  original and secondary exceptions remain visible.
- `session-owner-service-close.json`: root startup hash, adapter result and service
  generation. A first failure stays failed after late successful child cleanup.
  Publication failure is itself unverified, cached and raised; existing files
  are not overwritten.

The actual V12 finish/save-fixture fence also checks backend service custody
when the local Executor obligation is empty. V15 finalization preserves the
primary exception and both scorer/source finalizer failures. Cleanup never
adds input authority. No automatic kill or retry is introduced. File fsync and
exclusive publication do not establish Windows directory/power-loss durability.

## Conditions, outcomes and limits

H: explicit session selection can preserve owned-service startup/close custody
and prevent control effects when adapter release remains unresolved.
T: current-source option/finalizer tests plus real owned Python services,
private sockets and actual Backend/Executor with parent/child Fake X fixtures.
D: correct selection/manifests, joined receipts, owned exit, immutable failed
release and publication outcomes, and refusal before finish/save fixture effects.
C/U: inert option tests substitute base.main; no Vizdoom/session/controller/game
entrypoint, real display/input, WSLc, Docker, model or provider is run. The actual
wrapper/backend uses Fake X and a synthetic capture. This does not prove physical
release bounds during blocked platform I/O, actual controller/session death,
useful application response, independently checked task success or economics.

Normal and optimized Python each passed **208 methods / 27 modules**, zero skips.
The timing instrumentation from #9001 remains in the composed source and suite.
Ten session rows distinguish normal close, blocked close, startup failure,
startup artifact collision, close artifact collision, command selection, V15
selection/source pins, adapter-obligation effect fence and paired/finalizer errors.
The normal and blocked cells retain parent PNG/.ait capture, child input edges,
accepted intent/source, startup/control/recovery/finish and root close receipts.
Blocked close remains failed even though eventual child cleanup is verified.

## Independent saved readback

`read_saved.py` imports only standard-library saved-data helpers. It checks raw
file hashes, independent PNG RGB reconstruction, capture/admission/owner joins,
session/child startup and close hashes, original control failure, publication
collisions, primary/finalizer markers and exact row inventories. The reused
backend reader is adapted only to the new suite counts; its original is retained.
Both reader modes pass and reject **15 mutations per report**.

The final parent has **96 LF source pins**, with **99 files** in the frozen union
of parent/child/manifests. `source-index.json` separately binds raw source bytes
and LF-normalized bytes: V15 manifests hash raw bytes, while process evidence
uses LF pins. A reader initially failed to normalize Windows separators in the
legacy manifest; its source/output are retained, and the corrected reader does
not alter the original manifest.

`named-pid-absence.json` queries only the **56 recorded owned child PIDs** after
the owned handle joins. All were absent at that timestamp. This supplements
handle-based lifecycle evidence; it is not native PID start-time proof or a
process termination operation. `pid-source-readback.json` binds its input IDs.

First missing-module/effect/finalizer/import failures and old-base outputs remain
under `exploratory/`. `driver.py.txt` is the guarded current-suite driver.
`SHA256SUMS.txt` inventories this entire new packet, excluding itself.
Generated `__pycache__` is excluded and the saved reader disables bytecode writes
before importing its helper. The initial publication accidentally tracked two
generated cache files; their original bytes remain in commit
`17c9dc05457125dc7db664274ae0dc13071c0a0f`, not in the corrected evidence inventory.

Next: qualify actual controller/session failure through the explicit selected
path, then native environment response/release/effect under applicable conditions.
The full control and matched-efficiency goals remain open.
