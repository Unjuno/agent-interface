# Supervised Win32 standard-caller trial R02

This is a fresh, one-shot user-authorized native Windows fixture trial of the
`--session-mode supervised-win32` public stdio MCP route. It follows R01, whose
preserved failure exposed a deterministic collision between the public call
receipt directory and the native producer result directory. Commit
`5da333c6bfc43dea34c82b251b2281aead254ed3` separates those namespaces and
adds a regression test.

R02 asks whether the standard caller carries a fresh observed HWND generation
through validation and dispatch, retains exact producer exit, verified input
release and an independent neutral-state readback, and causes the owned fixture
to record the exact requested save effect. Its task text and run directory are
unique to R02. The caller retrieves the same call after its single dispatch and
then closes the supervised session. The fixture effect file and event journal
are the independent task oracle. The probe restores the prior foreground
window when it remains available.

The condition packet freezes the source commit, exact task, operation sequence,
timeouts and fail/unknown rule. `probe.py` and `audit.py` are frozen before any
fixture is created; `SHA256SUMS.freeze` binds those inputs. The probe retains
both the public response envelope and its raw dispatch report. `raw.json`,
`audit.json`, and `SHA256SUMS` are produced after the single run. A failed or
incomplete attempt remains the result; this directory is never reused.

This trial does not test cancellation or blocked-I/O recovery. It does not
establish an atomic generation fence, a hard physical release deadline, MAP01,
runtime-integrated task success, efficiency, or broad reliability. It uses no
WSLc or Docker allocation.
