# X11 OOD manifest tamper audit

## H/T/D/C/U

- H: the source-bound SHA-256 manifest catches frame and receipt tampering.
- T: verify the 160-frame fresh manifest normally, replace one frame byte, and replace one receipt SHA.
- D: same fresh X11 raw frames and manifest; no model rerun.
- C: integrity-only result, not semantic/runtime evidence.
- U: normal pass and both tamper cases must be detected.

## Result

| check | result |
|---|---|
| normal manifest | PASS |
| tampered frame | rejected |
| tampered receipt SHA | rejected |

This audit strengthens evidence provenance only; #2409's bounded OOD scope and no-promotion boundary remain unchanged.
