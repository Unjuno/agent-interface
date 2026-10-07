# Bounded app-server pipe sends composed with reply admission

Parent: [#57](https://github.com/Unjuno/agent-interface/issues/57). Worker e0cc/root and existing bugbot are coauthors. Policy FINAL-v5. This is ordinary transport repair with benign local subprocesses; no formal allocation was consumed.

A live child that stops reading stdin defeats the previous request timeout: that timeout started only after synchronous write/flush. This composition adopts the existing #7305 nonblocking pipe-send mechanism on the #8298 response-admission client. A timed-out or otherwise uncertain send quarantines later sends, and owned POSIX stream closure waits for the active writer before retiring its descriptor.

## Sources and scope

| Input | Immutable commit | Use |
|---|---|---|
| #8298 | `576f32347c9f2c8ad948999d55bfc7b60ecd8612` | PR base; first numeric reply, pending-ID ownership and retirement |
| #7305 | `2538aafc743bcf16b245ea426d419439ed01be15` | Nonblocking send, common request deadline, uncertainty quarantine, send snapshot, runtime eligibility, four test suites and UTF-8 fixture |
| #8290 | `c6f5a122afee85e44bec5c39b80f02e6b939d56a` | Exact exited-leader reap helper and expanded process-tree tests |
| Main at intake | `349dd5f80beaa870dcc97133237cc48c1e979d23` | Duplicate/current-source inspection, not this stacked PR base |

The executed candidate and final client have SHA-256 `3994bd0a1ab956cc472e06687355c3247168d606d141064fbaa03b6da1da9bce`. The #8298 reader and #5156 numeric-ID fixture remain unchanged. The native catalogue gains exactly five registrations. No predecessor branch or historical evidence is rewritten. This is composition and regression repair, not a new pipe-send mechanism.

The public API keeps `request(..., timeout=30)` and adds `notify(..., timeout=30)`. Timeout values must be finite nonnegative int/float values within the threading lock range. Native sends use an exclusively owned fd-backed stdin pipe; custom write/flush-only streams fail explicitly before journaling/admission. Custom factories continue to own their stream wrappers. Windows sends require Python 3.12+, but real Windows pipes and Windows cleanup were not exercised here. Owned descriptor-custody validation is POSIX-specific.

## Prospective discrimination and observed result

`PLAN-v1.json` in the archive fixes H/T/D/C/U, the six cells, source/harness hashes and stop/rescue rules before execution. H: the existing bounded sender composes with current reply ownership and retirement. T: one healthy Unicode/float-ID, one 512 KiB send to a nonreading peer, and one send/concurrent-close cell per arm. D: candidate returns typed uncertainty without rescue, refuses follow-up without another journal row, preserves healthy data and retires observed actors. C/U: synthetic backpressure, scheduling and instrumentation; no independent kernel byte count, provider, GUI or task-effect measurement.

All six outer wrappers exited 0 with empty harness error lists. This wrapper success includes the deliberately rescued failing baseline.

| Case | #8298 baseline | Composed candidate |
|---|---|---|
| Healthy Unicode reply and numeric float ID | Exact text/hash | Exact text/hash |
| 100 ms timeout, nonreading peer | Still blocked at 600 ms; owned-child kill rescue required | `AppServerWriteUncertain` at **102.541458 ms**; no rescue |
| Follow-up after candidate timeout | Not attempted after baseline rescue | Rejected as previous-send failure; journal unchanged |
| Concurrent close during active send | Close returned; writer got `BrokenPipeError` | Close returned; writer got typed uncertainty |

The candidate reported 65,536 of 524,345 bytes for the blocked frame and 65,536 of 524,351 for close cancellation. Those are client-observed write counts, not proof of peer acceptance or completed effects. Every cell records the child and reader retired, streams closed and pending/cache empty; concurrent request/close threads also retired. The baseline close did **not** hang in this experiment.

Environment: macOS 27.0.1 arm64, bundled CPython 3.12.14, monotonic nanosecond timing; one serial run per arm/case, fixed 50 ms construction interval before concurrent close. These single-cell results establish the regression here, not a latency distribution or speedup. The 102.54 ms result is not a hard 100 ms wall-clock guarantee.

## Validation and retained failures

- 78 focused protocol/catalogue methods PASS in normal Python and 78 PASS under `-O`; 22 workspace methods PASS; committed workspace index reaches 160 directories.
- Changed Python compilation, diff whitespace check, unchanged-reader/#5156 checks, exact #8290 helper and five-only catalogue registration checks PASS.
- The controlled writer-lock regression fails with the old close method and passes with descriptor custody. On timeout, close leaves owned streams alive for the suspended writer and a subsequent close can retire them safely.
- The original custom-stream/EOF fixture failures, #7305 baseline failures, close ablation failure and sparse-checkout/import-path failures are all retained. Read `CORRECTIONS.md` before interpreting counts.
- Saved-data coauthor audit v1 checks 77 items but contains an incorrect no-follow-up interpretation. Its additive v2 checks 5 items and corrects that interpretation using the existing raw. Root also checked source identity and retirement. These are construction/readback checks, not nonauthor quorum votes.

No whole native suite or live Codex/model/GUI run was performed. Serialization, journal writes/locks, condition scheduling and callbacks remain synchronous; the request and close APIs do not promise one hard whole-call wall-clock bound. Close can spend its timeout in multiple preexisting process/reader phases. Response admission remains a local classification point, not physical wire authentication. Unknown delivery is never silently replayed.

## Evidence and review boundary

`evidence.tar.xz` contains source snapshots, harness, six raw/journal pairs, wrapper receipts, first failures, final logs, source checks and coauthor readback. `manifest.json` lists every member's size and original/projected SHA-256. The declared projection replaces local task/home paths only; original private evidence remains unchanged. Hashes inside historical records continue to name the original bytes. Source blobs and journals are unchanged by projection. Archived Python is passive evidence; do not execute the actor harness to verify the package.

Run `python3 verify_evidence.py` for bounded, read-only archive/hash/receipt/source/result verification. It does not extract or execute archived code. Integrity checks support traceability, not external attestation of the original run.

Publish as a Draft stacked on #8298. Main integration requires a fixed genuine nonauthor committee and votes, current-main combined-tree validation, effective mandatory gates and a forward-only conditional update under FINAL-v5. Coauthor checks do not satisfy those gates.
