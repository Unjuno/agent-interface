# Frozen execution environment

- Host: Windows 11, build `10.0.26300`, AMD64.
- Interpreter: CPython `3.13.14`, 64-bit, MSC v.1944; reported by `sys.version`.
- Resolved executable: `C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0\python3.13.exe`.
- Executable SHA-256: `ad169f4cb4bfb78c7a5c030a4529c19d6643276778e33994c93e145b6191c3ec`.
- Invoker: `C:\Windows\py.exe -3.13` resolved that exact package executable. Formal commands invoke the resolved executable path directly, bypassing launcher ambiguity.
- Dependencies: Python standard library only. No third-party packages are imported by candidate, runner, or auditor.
- Execution: one local CPU process for the candidate, then one local CPU process for the auditor. No container is needed because the hypothesis concerns deterministic analytic rendering/control, not container semantics.
- Explicitly unused: WSLc, Docker/OrbStack, GPU, model service, GUI, OS input, human, network, or live application.
- Machine memory, CPU model, and host contention were not frozen or measured; no performance/resource-isolation claim is made.

The WindowsApps launcher alias at the user path was zero bytes; it was not used as the frozen executable. The resolved WindowsApps package binary above was measured and hashed before formal execution.
