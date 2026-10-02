# Issue #2437 Allocation 03 — audited scoped failure

## Result

Disposition: **`FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED`**. The independent raw-only auditor ran exactly once, returned `errors=[]`, and recorded the raw as 2,144 bytes with SHA-256 `375a41d1d7489dbbc9305d4d8fe58a36212fa066928b509d3af8e47dc0a7e4ef`. The frozen candidate exited 0 and was invoked once.

The auditor's validated predicates establish this bounded failure: an XTEST F8 key-down was independently observed before and after SIGKILL of the backend-owning process; that process exited by SIGKILL while the same Xvfb server PID remained live; a distinct replacement process/session received the byte-identical request created before failure, with its monotonic lease still unexpired and the old observation/binding identities unchanged; the replacement session began without recovery quarantine, completed that stale request and emitted input; a later independent Xlib query after explicit observer-owned release verified neutral key state. This is an Xvfb logical-state observation, not physical hardware sensing.

The reported test condition is met: **a backend-process restart can accept stale authority while the prior key remains down** on this exact runtime/Xvfb path. This is a scoped safety FAIL, not proof of a physical stuck key, not a claim about native compositor behavior, and not a production-wide conclusion. Keep Issue #2437 open for other failure boundaries and integration decisions.

## Allocation history (not pooled)

| Allocation | Frozen base | Candidate | Auditor | Disposition |
|---|---|---:|---:|---|
| 01 | `d1dc9b8e6cc1e165d353f086b530a0024277b7f6` | 0 | 0 | `STOP_MAIN_ADVANCED_BEFORE_LAUNCH`; main advanced to `d077494` |
| 02 | `d077494b50341f638e6d66f63e817ec48923768d` | 1, exit 0 | 1 | `STOP_AUDIT_ERRORS`; parent evidence assembly omitted required fields; raw preserved unchanged |
| 03 | `d077494b50341f638e6d66f63e817ec48923768d` | 1, exit 0 | 1 | `FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED`; errors 0 |

Allocation 02's raw was not re-read or re-run. Its source-level recording defect and preformal fix are retained separately. Allocation 01's main-drift STOP is preserved verbatim. Only Allocation 03 supports the scientific FAIL above.

## H / T / D / C / U

- **H:** With Xvfb alive, killing only the X11 backend owner while F8 is held may leave the server key-down and let a fresh owner accept the old, still-valid request without a fresh observation.
- **T:** One precreated valid request; backend child emits F8 down; independent Xlib observer samples; SIGKILL; server PID and key state sampled; second process/session dispatches byte-identical request; independent explicit release and neutral readback. One candidate invocation followed by one raw-only audit.
- **D:** Auditor verified the stale request was admitted and emissions increased while all identity, timing and cleanup gates passed: scoped **FAIL**. No other outcome is inferred.
- **C:** XTEST/Xvfb maintain logical server state; process death, server restart, synchronous pointer grab, native compositor and physical devices are different boundaries. The observer is a separate X connection, not hardware instrumentation.
- **U:** One WSL2 Ubuntu 24.04.4 x86_64 host, CPython 3.12.3, python-xlib 0.33, private Xvfb/Tk fixture, F8. No Windows native input, real compositor/device, model, application task-quality, latency or user-facing reliability claim. Supervisor/host death, multiple controls and delayed cleanup remain untested.

## Method and audit discipline

The V3 freeze and source hashes are committed before its single formal invocation. Ten auditor/record-assembly construction tests and the no-input fixture preflight passed before the run. Allocation 03 used a private WSL Xvfb because #5085 did not assign this work a shared Docker/OrbStack slot; Docker Desktop was not used for the experiment. The raw-only auditor read Allocation 03 raw once and generated `AUDIT.json`. No candidate, test, parser or auditor subsequently read it. The raw is included below as an opaque byte-preserving publication object; its scientific interpretation comes only from the retained audit receipt.

**Publication protocol STOP:** an attempted GitHub blob readback automatically surfaced the uploaded UTF-8 JSON as decoded content. A transfer-equality check parsed that response after the one-shot audit, contrary to the freeze's no-post-audit-parse gate. No new scientific verdict was computed and the original local audit receipt is unchanged; however, overall delivery status is `STOP_POST_AUDIT_RAW_READBACK`. The remote blob SHA is retained, but independent byte-for-byte publication verification is not claimed. No further raw readback, audit or candidate rerun will be attempted.

No source/runtime change is proposed by this evidence PR. The result supports investigation of a shared restart/quarantine contract, but remediation and broader failure-boundary coverage require separate engineering and integration review.
