# Win32 target-incarnation cookie R02

R02 corrected R01 by loading `advapi32`, but did not assign it to the backend
fixture. The production identity path again stopped before generation; the
probe destroyed its own hidden HWND successfully. No input was sent and no
existing window was targeted. Preserve [raw.json](raw.json); do not replay R02.

Raw receipt SHA-256: `8ce8b3d27711573c014c3a3886656c3ae4ac11e5ac1008ca0256dccc837a459c`.
