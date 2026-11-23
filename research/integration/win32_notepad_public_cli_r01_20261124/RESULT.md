# Win32 public runtime CLI Notepad task R01

**Disposition: SETUP_STOP; no task action dispatched.** Frozen source main was
`22aba58c276141401a7688be335be5191ec661b9`; the runtime zipapp was built from
the same runtime source tree at `f7c6b5832d726ad110ce40d311bdec674eb3d0d6`.
Its manifest audit checked all 64 packaged runtime files against the frozen
main and passed. The exact zipapp SHA-256 was
`64084e8ab0b74a25441dfc3e63893e526cd7ac76035821c5a67897ed06518d9e`.

After launching one fresh Notepad window, the one allowed public CLI
pre-observation failed with
`ModuleNotFoundError("No module named 'runtime.backends.win32_v1.capture_artifacts'")`.
The runtime report is `observation_failed`, `input_dispatched=false`; no
dispatch call was made. The actual unique target filename was
`task-r01-6C2D9E.txt`, which differs from the placeholder filename in the
frozen conditions; the observed file remained 0 bytes. The expected HWND/PID
and executable path matched at stop review. Only that exact target was closed
with normal `WM_CLOSE`, and the close receipt confirms the window is absent.

The package builder's promoted Win32 source list omitted
`runtime/backends/win32_v1/capture_artifacts.py`, although the backend imports
it during observation setup. This explains the setup failure; it does not
show that runtime doctor passed incorrectly or establish any task, release,
recovery, caller, or efficiency outcome. R01 is not retried. The packaging
repair and regression test are a candidate for a separate follow-up attempt;
the R01 record remains failed and its raw files are retained under `run/`.

See [CONDITIONS.md](CONDITIONS.md) and the raw receipts in `run/raw/`.
