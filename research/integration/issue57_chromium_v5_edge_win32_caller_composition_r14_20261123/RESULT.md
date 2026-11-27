# R14 result: computer-use activation was blocked

Date: 2026-11-23 (Asia/Tokyo)

## Outcome

**STOP before desktop capture or task input.** The standard-Python run launched
both isolated cases and wrote their `activation-request.json` records. Each
waited the frozen 120-second CUA handoff period without an activation
confirmation and then stopped. The CUA tool had inventoried the exact isolated
Edge window, but selecting it with `getApp` was blocked because the tool could
not determine the active browser URL with sufficient confidence. No CUA click
occurred. The optimized-mode run was not started.

Both raw cases record zero task operations and POSTs, successful deletion of
their unique Edge profiles and restoration of the prior foreground window.
Edge was `157.0.4341.60`; no provider/model calls occurred. The frozen source,
protocol, raw requests, run records and hashes remain available here. The
active Edge window and profile disappeared after the timeout cleanup.

## Interpretation

R14 does not test desktop capture, native task input/release, task effect or
generation-change refusal. It establishes a concrete environment boundary:
this computer-use route will not activate the isolated Edge window while its
browser-URL policy check is uncertain. No alternate UI or foreground bypass
was attempted. Continue independent offline/repository work; a later live
attempt requires a computer-use path that can establish the target window
context without violating that policy.

## Frozen artifacts

- Protocol: [PROTOCOL.md](PROTOCOL.md)
- Harness and protocol freeze: commit `a53e218805d19e21346e89a17430d8764d943305`
- Standard-mode raw cases: [raw/normal](raw/normal)
- Raw SHA-256 manifest: [SHA256SUMS.json](SHA256SUMS.json)
- Standard-Python unittest exit: 1; both cases failed at the documented CUA
  activation timeout. The `-O` run was not attempted.
