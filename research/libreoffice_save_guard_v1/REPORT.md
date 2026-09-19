# LibreOffice save guard v1 — advisory flock and post-open file lease

Status: **FAIL generic inode-scoped OS guards at this save boundary.** `flock` is `PERMISSIVE_STALE`; a Linux write lease is `UNAVAILABLE_POST_PRECHECK` once Calc already has the document open. HOLD broader OS-mediation designs.

Immutable experiment BASE: `3c6f07f0660aee854d6b2d2d0f525fd9f451de68`. Branch: `research/libreoffice-save-guard-3c6f07f`. New files only under `research/libreoffice_save_guard_v1/**`.

## Why this rung

PR #274 retained a concrete stale-effect counterexample: LibreOffice 25.2.3.2 can silently overwrite a relevant same-inode external XLSX rewrite if the file mtime is restored to the plan-time value. PR #273 separately tests a cooperative application-owned conditional effect endpoint. This block asks a narrower boundary question: can common Linux file guards inserted **after the final precheck** supply enforceable effect authority without application cooperation?

## Rung A — advisory `flock`

One frozen stable→stale pair. Both arms acquire `flock(LOCK_EX|LOCK_NB)` on the task path after the final GUI/file precheck and hold it through Ctrl+S, the known `Confirm File Format` response, durable XLSX scoring, and input-release verification.

The stale arm reproduces the #254 pair-06 adversarial condition: a separate valid XLSX is written into the same inode, `fsync`ed, then the exact precheck mtime is restored before lock acquisition and Save.

| arm | lock acquired | final modal after format confirm | durable XLSX | disposition |
|---|---:|---|---|---|
| stable | yes | none | `office / preview` | normal save |
| stale_restoremtime | yes | none | `office / preview` | **PERMISSIVE_STALE** |

The decisive mechanism evidence is inode identity:

- stable: lock fd inode `786667` → final pathname inode `786790`;
- stale: lock fd inode `786671` → final pathname inode `786918`.

The lock remains attached to the old inode while LibreOffice's save installs a new inode at the pathname. The stale arm's external SHA-256 `08c8ddd4ef6e08ba523c3a5d833d19b9fe3381e0918e5c27ebbf57aafc022afb` is replaced by final SHA-256 `5db614d5b565f962ac9c695fe8243f9b07c334196f5569dc3af552676ffb23fa`, independently read as `A1=office`, `A2=preview`.

**D:** `flock` is not an effect-commit guard for this path. The observed inode transition is sufficient to explain why an inode-scoped advisory lock does not cover the final pathname; no undocumented LibreOffice-internal claim is needed.

## Rung B — Linux write lease acquisition after precheck

A separate single-arm allocation opens Calc, performs the same in-memory edit, records the final precheck, then attempts `fcntl(F_SETLEASE, F_WRLCK)` on the task file. It performs no Save and no external mutation.

Result:

- `F_SETLEASE`: failed with errno 11 `EAGAIN` / `Resource temporarily unavailable`;
- `F_GETLEASE`: `F_UNLCK` (2);
- file stat/hash unchanged;
- Calc remained alive;
- terminal X input release verified empty.

A construction-only same-filesystem positive control acquired a write lease on an otherwise unopened private file (`F_GETLEASE == F_WRLCK`). Thus the container/filesystem supports leases; the failure is specific to trying to install the exclusive lease at the required boundary after the GUI already has the file open.

**D:** `UNAVAILABLE_POST_PRECHECK`. The experiment intentionally does not redesign around pre-open leasing, because that changes the question and would interfere with opening/editing the document.

## Audit

The pre-frozen rung-specific audits passed. A separate post-outcome auditor does not import the experiment controller. It reopens the durable XLSX files, recomputes hashes/cells, checks the mtime/inode mutation invariant, lock-fd/path inode divergence, lease errno/state, exact retained backend Git blobs, Calc liveness and empty release. It also rejects four deliberate corruptions (stale classification, final pathname inode, lease errno, release verification). `AUDIT.json`: PASS.

Exact retained source identities:

- `backend_x11.py` Git blob `b4f8e043ce4f8929d446e038418ea0fd3655bab0`;
- `office_backend.py` Git blob `3aeca10f62fb1366bcdd5fad561509cfcc0d91ab`.

## H / T / D / C / U

**H.** A generic OS file guard that can be inserted after client precheck might prevent a stale non-cooperative GUI save without requiring an application-owned conditional commit.

**T.** First `flock` pair, then one post-precheck write-lease acquisition probe. LibreOffice 25.2.3.2, openpyxl 3.1.5, private Xvfb/Openbox, root-run application, overlay filesystem, no model/network/user files. First outcomes retained; no allocation IDs rerun.

**D.** FAIL the two tested inode-scoped candidates for the required boundary: advisory flock is permissive to stale overwrite; exclusive file lease cannot be installed post-precheck. This does not prove every OS mediation primitive fails.

**C.** A pathname/directory/filesystem mediation layer (for example a privileged filesystem broker) could cover rename-based commits, unlike an old-inode lock. Such a mechanism would be substantially more invasive and would need its own small experiment. A controller that observes invalidation before issuing Save can simply refuse input; this block specifically concerns commit protection when relying on the ordinary application's save path.

**U.** One LibreOffice version, overlayfs, root process, one stable/stale pair, no real concurrent race-frequency estimate. No fanotify/FUSE/LSM/immutable/permission mechanism was tested. Bind-mount construction is unavailable in this container (`mount --bind`: permission denied), and `chattr` is not installed; those are environment facts, not scientific results.

## Next question

Do **not** stack more inode locks. The next high-information step is architectural: either test a pathname-level mediator that actually owns the save commit, or treat ordinary GUI save as lacking an authoritative commit boundary and fail closed/escalate when such a mediator/application endpoint is unavailable. Any pathname mediator should first be tested in a tiny file-writer fixture before another LibreOffice allocation.
