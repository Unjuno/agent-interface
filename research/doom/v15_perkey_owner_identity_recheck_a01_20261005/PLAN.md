# V15 per-key owner identity recheck — follow-up

This is a follow-up construction recheck of the owner-selection defect recorded in PR #8079. It is not a preregistered or formal allocation; the outcome gate was inherited from the earlier evidence package before this current-head rerun.

- **H:** The combined V15 plus `--per-key-input-measurement` startup on the latest PR #8065 head still selects current raw V12 through Python's module cache instead of the requested archived A01 measurement owner.
- **T:** Freeze PR #8065 head `4158d9b063e7cbf56828f1b0667ec2714af0ff2b`. From 56 source files extracted byte-for-byte from that commit, run the exact startup probe in three fresh Python processes: V12 per-key, V15 default, V15 per-key. Stop at `suite.Session()` before session or owner construction. Preserve a system-Python dependency failure and complete the same probe with bundled Python 3.12.14/Pillow 12.3.0.
- **D:** The source-selection defect is reproduced if V12 per-key selects the archived A01 owner, V15 default retains the current V4 transition owner, but V15 per-key selects current raw V12 while its manifest records the archived A01 hash. No X11, GUI, game, model, input, or owner thread may start.
- **C:** This only tests import/backend selection at one startup boundary. It does not test release method execution, physical state, application consumption, or cancellation.
- **U:** The run is local source-level construction evidence. It does not close the live threat-response, useful-feedback, recovery, latency, or MAP01 gates.
