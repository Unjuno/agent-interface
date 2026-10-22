# Frozen execution environment

- Host: Windows 11, build `10.0.26300`, AMD64.
- Interpreter: CPython `3.13.14`, 64-bit, MSC v.1944.
- Resolved executable: `C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0\python3.13.exe`.
- Executable SHA-256: `ad169f4cb4bfb78c7a5c030a4529c19d6643276778e33994c93e145b6191c3ec`.
- Invoker `C:\Windows\py.exe -3.13` resolved the executable; formal commands invoke the resolved path directly.
- Dependencies: Python standard library only for candidate, runner, and auditor.
- Execution: one local CPU process for candidate, followed by one local CPU process for the independent auditor. No container-specific behavior is under test.
- Explicitly unused: WSLc, Docker/OrbStack, GPU, model service, GUI, OS input, human, network, or live application.
- Machine memory, CPU model, and host contention were not frozen or measured; no performance or resource-isolation claim is made.

The user-path WindowsApps launcher alias was zero bytes and was not used as the frozen executable. The resolved package executable above was measured and hashed before formal execution.
