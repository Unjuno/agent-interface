# Win32 target-incarnation cookie R01

This was the first no-input native check of the new target property. It created
one hidden `STATIC` HWND owned by the probe process. Backend setup stopped
before the generation query because the probe omitted the `advapi32` handle
required by the production process-identity path. The `finally` block destroyed
the owned HWND successfully. No input was sent and no existing window was
targeted. Preserve [raw.json](raw.json); do not replay R01.

Raw receipt SHA-256: `24954689b1b0334160190c36b6bf62d68f7df6628fde8ad0b08f24fd01ae89e2`.
