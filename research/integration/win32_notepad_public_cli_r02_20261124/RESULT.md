# Win32 public runtime CLI Notepad task R02

**Disposition: SETUP_STOP; no observation or input was attempted.** R02 froze
the repaired zipapp candidate at source revision
`e48f1fda8fdc9695f702d6004a0aa36a6a1e0037`. Its deterministic artifact is
790,952 bytes, SHA-256
`56ced08ca480dd2217d606328fefda5d30d0ff0d304b6db4c4bfa2431a4e596b`;
all 65 packaged source files match baseline main
`22aba58c276141401a7688be335be5191ec661b9`. Runtime doctor selected the
promoted Win32 backend without side-effect authority.

The frozen condition named `task-r02-8A41D7.txt`, but the target launcher
created `task-r02-6C2D9E.txt`. The target receipt was inspected before any
observation, the file remained 0 bytes, and the exact HWND/PID/process path
matched at stop review. No runtime observation or dispatch was invoked. Only
that owned window was closed using normal `WM_CLOSE`; its close receipt
confirms it is absent. The R02 pre-input snapshot predates the launcher and
therefore says `target_launched=false`; the subsequent launch receipt records
the actual setup state. This is a harness naming defect and condition
deviation, not a runtime result. R02 is not retried.

R01's packaging omission is fixed and local distribution tests pass, but
end-to-end Win32 observation and task effects remain unverified. See the
[frozen conditions](CONDITIONS.md) and raw setup receipts in `run/raw/`.
