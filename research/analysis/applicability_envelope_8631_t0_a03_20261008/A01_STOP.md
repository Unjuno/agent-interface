# T0 A01 — STOP, auditor input contract

Frozen main: `3daf9e167f1e7896ad682ac1d22134618f70a23c`. Candidate invoked once and exited 0; it reported 3/3 positive train rows and counterexample F1. The independent auditor invoked once and exited 1 before any audit because the harness supplied candidate JSON as argv text while the auditor tried to read argv[2] as a path (`OSError: [Errno 22] Invalid argument`). No audit verdict, retry, or scientific result.

- Candidate stdout SHA-256: `777B4C65FBBE61094C2E3E4DFBCB6BEE4A14EA69E740AB5F22FF32219B34FF72`
- Fixture SHA-256: `180238D9E10A459F4C7789D3256EC23087AA8EBE116A93259964CB011DA1E2F2`
- Candidate script SHA-256: `159C39A5158B3F0E194881AAEBB9B6E5AC6449D6CB0C65C41964C6BE3FD5D224`
- Auditor script SHA-256: `D059081D498467F5C1F44760D17D9A31E0DC222B410C1F441EAA045C30F03F9E`

Disposition: `STOP_AUDITOR_INPUT_CONTRACT`. A01 remains immutable in meaning and is not promoted by A02/A03.
