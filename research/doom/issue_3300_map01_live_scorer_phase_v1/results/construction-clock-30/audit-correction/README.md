# Additive run-30 audit-label correction

The immutable original `audit/audit.json` and GitHub comment retain the
historical decision label `HOLD_PASSIVE_ASYNC_TIC_STATIC_PROCESS_IDLE`.
That label overstates what endpoint process-state/CPU samples and a static
Python API snapshot establish. Do not interpret it as evidence that the engine
clock stopped or remained idle during the full window.

The auditor now emits `HOLD_API_TIC_STATIC_PROCESS_ACTIVITY_UNRESOLVED` for
this retained raw capture. No raw fields or predecessor artifacts were
changed. Corrected stdout JSON SHA-256:
`421ac9aecd91e43c422e51988464c821a4a9cde5ebf13c07a3b32fbde52f061e`.
Auditor source SHA-256:
`b1d8961d4f96270d987adc3f95f1acc827ae2d34b9abaf9a70d38b404d791d8f`.
Focused test source SHA-256:
`6effef02da792a71d1bf86c04d4577074a04f18de03b73d4dc9ac6976a13cc63`.
The 23-test suite passes in the isolated arm64 image documented for run 32.

This correction remains `formal_allocation: false` and does not establish a
live tic witness. See `../INTERPRETATION_ERRATUM.md` and runs 32–33 for the
separate follow-up evidence.
