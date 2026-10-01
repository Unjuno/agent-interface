# Pre-run freeze correction 01

The initial source commit `90ca78b6de3235a975cf214ea11262a1f20110ef` omitted the post-split `PROTOCOL.md` digest in `FREEZE.json`. This mismatch was detected before any formal candidate or auditor container was invoked (formal candidate=0, auditor=0). The candidate, auditor, fixture, truth sidecar, and hypothesis were unchanged; only the recorded protocol hash and this correction receipt are updated in the successor freeze commit. The initial commit is preserved in Git history and the allocation remains unconsumed.
