# Supervised Win32 standard-caller trial R01

This is a one-shot user-authorized native Windows fixture trial of the
--session-mode supervised-win32 public stdio MCP route. The frozen question
is whether the standard caller carries a fresh observed HWND generation
through admission, retains exact producer exit and separate neutral-state
readback, and causes an independently inspected fixture save.

The trial uses only a fresh runtime.backends.win32_v1.fixture_app process
owned by probe.py. The public caller observes the fixture, copies the returned
generation into the program source, validates once, dispatches at most once,
retrieves the same call if the first response is pending, and closes the
supervised session. The fixture's effect file and event journal are the
independent task oracle. The probe records and restores the previous foreground
window when it remains available.

The condition packet freezes the exact source commit, task, operation sequence,
timeouts and fail/unknown rule. probe.py and audit.py are frozen before any
fixture is created; SHA256SUMS.freeze binds those inputs. raw.json,
audit.json, and SHA256SUMS are produced after the single run. A failed or
incomplete attempt remains the result; this directory is never reused.

This trial does not test cancellation or blocked-I/O recovery. It does not
establish an atomic generation fence, a hard physical release deadline, MAP01,
runtime-integrated task success, efficiency, or reliability. It uses no WSLc
or Docker allocation.
