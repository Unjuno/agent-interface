# Local offline harness invocations

The same test file was launched in both shells. It internally starts `powershell.exe` for the fake WSLc CLI.

- Windows PowerShell: `powershell.exe -NoLogo -NoProfile -NonInteractive -File .github/scripts/test_wslc_local_runtime_offline.ps1` — exit 0; stdout says `Offline WSLc smoke harness: PASS`.
- PowerShell 7.6.9: `pwsh.exe -NoLogo -NoProfile -NonInteractive -File .github/scripts/test_wslc_local_runtime_offline.ps1` — exit 1 before the harness starts; `Add-Type` rejects the `ConsoleApplication`/`WindowsApplication` output kinds. See the paired raw stdout/stderr and exit files.

No live WSLc action was part of these checks.
