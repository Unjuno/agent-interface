# R10 result: stopped before native input

Date: 2026-11-23 (Asia/Tokyo)

## Outcome

**STOP_SETUP; no task action was dispatched.** Standard Python started the
isolated Edge instance and reached its DevTools endpoint, but the harness did
not find exactly one visible top-level Edge window matching the fixture title
and launched-process PID within 12 seconds. The stop occurred before creating
`Win32Backend`, before observing or minting a target handle, and before any
native input. The changed-generation case and optimized-mode run were not
started. No retry was made under this R10 identity.

The raw `positive/run.json` records `TimeoutError: visible Edge fixture window
was not found`, zero minted handles, observations, admissions, dispatched
operations, native operations, POSTs or receipts. The unique Edge profile was
removed, and the previously foreground window was restored. The browser
reported Edge `157.0.4341.60`. The captured loopback DevTools endpoint was
ephemeral; this run made no model/provider call.

## Interpretation

R10 provides no evidence for native input, input release, task success, or
generation-change refusal. It is a useful setup failure that identifies the
window-discovery assumption as invalid on this host. R11 uses a separate run
identity and will require a visible window title plus proof that the window's
owning process descends from the process carrying this run's unique profile.

## Frozen artifacts

- Protocol: [PROTOCOL.md](PROTOCOL.md)
- Frozen harness: commit `7b111650d30f100154c1661f0b08b02c3e9f92bc`
- Frozen protocol and experiment source tree: commit
  `dcbdf201556af2d4a6afa70025882472aab866b3`
- Raw conditions and run record: [raw/normal](raw/normal)
- Raw SHA-256 manifest: [SHA256SUMS.json](SHA256SUMS.json)
