# Status note — post-formal freeze-integrity correction

This note supersedes only the **overall formal disposition** stated in `REPORT_02.md` / `RESULT_02.json`. Those original post-formal files remain unchanged for provenance.

## Final disposition

**HOLD_PUBLIC_FREEZE_SELF_HASH_MISMATCH**

Allocation01 remains `STOP_OUTER_EXECUTION_TIMEOUT / HOLD_EVIDENCE_INCOMPLETE`.

Allocation02 completed 18/18 cases, its raw-only audit has zero errors, all 13 evidence mutations reject, all 90 recorded actor/watcher/Xvfb exits are zero, and the frozen numeric scheduler gates are met by the retained rows. Those are retained observations.

However, publication readback before PR creation found that the publicly committed premeasurement document is not byte-identical to the local document whose SHA-256 was recorded in the publicly committed `FREEZE.json`:

- `FREEZE.json` declared local `PREMEASUREMENT.md` SHA-256: `a355748dc28c42ca559023446ca6db174a06e553e2a0ac4b28a85fc919f9f32e`.
- Local frozen file: 3,613 bytes, Git blob `d7a9a8152c2f5e93367b6e065bb0ce46438200bb`.
- Public preformal file: 3,612 bytes, SHA-256 `ca0d0697b677bf62fcc08998f2188fd5825af937ee7523402fb21242c5a174a0`, Git blob `7c51441aeffa22c7a9b98344d98614ae12cde006`.
- Exact difference: the local file has one additional blank-line byte immediately before `## Construction status before freeze`. The H/T/D/C/U text and numeric gates are otherwise identical.

The frozen decision required source/provenance identities to reconcile. They therefore do not. The completed scientific table is **not promoted to a formal PASS**.

No case is removed, replaced or rerun, and the public preformal file is not rewritten after the fact to manufacture hash agreement. A new allocation is not run merely to obtain a favourable status.

## Publication-only corrections

During post-formal evidence packaging, GitHub readback also caught one one-character Base64 transcription in capsule part01 and missing terminal newlines in parts04/05. These were corrected before PR creation. All six final Git blobs now equal the locally computed original-part Git blobs, and the manifest-bound capsule restores the original 39-file / 434,651-byte evidence corpus. These packaging corrections do not change the formal data, source, schedules, gates or the HOLD above.

## Scope

The retained numeric rows support a descriptive bounded scheduler observation: in this directed fixture GLOBAL_FIFO missed the 100 ms critical boundary, the two priority policies did not, and burst-3 DEADLINE_FAIR avoided the selected unrelated-state starvation seen under pure critical-head priority. Because the public freeze identity gate failed, these observations remain evidence under HOLD, not an accepted formal PASS.

Parent #2254 also remains independently open at its stronger model/task/effect boundary.
