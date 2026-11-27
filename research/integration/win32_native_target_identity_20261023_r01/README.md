# Native Win32 target identity probe R01

This one-shot probe uses the production `Win32Backend.process_identity()` and
`target_generation()` paths against a hidden `STATIC` window created and owned
by the probe process. It reads both values twice, then destroys its own HWND.
It does not activate a window, send input, capture the desktop, or target an
existing user window.

The probe tests native API wiring and repeatability for one live HWND. It does
not test HWND destruction/reuse, target safety under races, user input or
release, task effects, supervisor recovery, WSLc, MAP01, efficiency, or
reliability. In particular, equal generation values do not prove that an HWND
cannot be reused between observations.

Run exactly once from the repository root on Windows:

```powershell
$env:SOURCE_COMMIT = (git rev-parse HEAD)
python research/integration/win32_native_target_identity_20261023_r01/probe.py
```

`raw.json` is the first outcome and must be retained unchanged. The probe
refuses to run if that file already exists. No retries are part of this packet.

## R01 result

The first driver attempt failed before backend import or HWND creation because
the repository root was not on `sys.path`; the exact setup error is retained in
`attempt-setup-error.txt`. After fixing only that driver setup, the single
native run passed. It created HWND `50857832`, read PID `48448` and process
creation time twice with identical results, and obtained the same generation
digest both times. The production generation query includes the GUI-thread ID
in that digest. `DestroyWindow` succeeded and `IsWindow` returned false
afterward. The raw receipt is `raw.json`; its SHA-256 is
`1670b0d6c5bfa51daced691ae73d48e562d6c44f6b8bec8504b2f0507c35674a`.

The read-only receipt audit passes 8/8 checks. The production process-identity
and MCP backend-composition suites pass 12/12 tests normally and 12/12 under
`python -O`; both full logs are retained. Both packet scripts compile. These
tests do not establish real input, release, recovery, target-reuse detection,
task effect, or efficiency. The preflight driver failure occurred before any
live native attempt; the successful native attempt was not retried.
