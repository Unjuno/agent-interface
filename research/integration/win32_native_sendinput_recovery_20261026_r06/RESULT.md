# R06 result — supervised Win32 recovery at the SendInput call boundary

**Scoped result: `PASS_SCOPED_BOUNDED_RECOVERY`; independent audit: pass.** One new, repository-owned Win32 fixture process was bound by native process/window generation. The standard public MCP caller observed the same generation. A real SHIFT-down was visible while the producer was held at a producer-local Python replacement for `user32.SendInput` at SHIFT-up entry. One public cancel returned `pending` in 0.460 ms; that response alone did not claim recovery. Later `interface_results` reported the exact action as `recovered`, the producer was retired (exit −15), release was confirmed, replay stayed denied, and task success remained null.

Owner recovery completed 17.2147 ms after cleanup was requested, against the configured 3,000 ms deadline; the measured margin was 2,982.759 ms. A separate Win32 state query 9.043 ms later saw SHIFT-up with the same target generation and native window/process witness. No emergency release was needed. Only the fixture `ready` event was recorded, no effect file appeared, the fixture exited with code 0, and foreground restoration returned to the prior HWND. All 13 raw files and all three pretrial files match their SHA-256 manifests; the independent audit checks pass.

The runner retained the internal template labels `r05-owned-fixture` and `r05-held-shift-recovery` after it was copied into the distinct R06 packet. The attempt ID, output root, fresh fixture PID/HWND, target generation, and MCP call IDs are distinct and cross-checked. This naming carryover does not change the input target or observed result, but is retained as a labeling defect in the audit trail.

The public cancel response remained `pending` while asynchronous cleanup ran; the retained terminal record supplies the recovered outcome. The later session-close receipt says `release_confirmed=false` because close did not perform a new action-level release; it is not substituted for or used to invalidate the retained recovery and independent key-up readback.

## Scope limit

The producer fault was an injected Python callable that stopped before entering native `SendInput`; the supervisor recovery and key-state readback were real Windows operations. This demonstrates bounded release for this specific standard-caller boundary fault on one workstation. It does not demonstrate an OS/kernel-level `SendInput` hang, an arbitrary platform-I/O bound, task completion, AppServer/model integration, MAP01, WSLc, efficiency, or a reliability rate. No WSLc allocation or Docker was used.

R05 is preserved as a distinct no-input harness failure. See [R05 assessment](../win32_native_sendinput_recovery_20261026_r05/ASSESSMENT.md). Its raw evidence was not retried or edited.
