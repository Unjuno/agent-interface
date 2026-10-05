# A03 result

**Disposition: `PASS_NATIVE_FOREGROUND_REFUSAL`, scoped to the native Win32
foreground-check path.** The independent audit is `results/a03/audit.json`.

The parent session switched the actual foreground to the decoy fixture, then
reached the instrumented `SendInput` boundary once. The sentinel returned zero;
the session failed with `SendInput failed error=0`, and terminal release verified
empty key/button state. This is the expected baseline RED.

The candidate observed the same real HWND switch, refused with
`foreground focus changed: expected <target>, got <decoy>`, and made zero
`SendInput` calls. It returned `execution_failed`, verified empty terminal
release, zero transition rows and no effect files. This is the candidate GREEN.

Both runs used two self-owned fixture windows. `SendInput` was stubbed in both
runs, so no OS keyboard or mouse input was emitted. The probe does not establish
input delivery, physical state, application task effect, natural focus-churn
coverage, or elimination of the check-to-insertion race. The A02 source-prep
STOP remains separately retained and was not retried.
