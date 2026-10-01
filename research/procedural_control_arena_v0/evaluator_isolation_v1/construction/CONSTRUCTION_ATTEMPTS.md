# Construction attempt ledger

These are disposable harness bring-up attempts. They are not the preregistered seed-2001 formal allocation; the formal no-retry rule was not invoked.

| Attempt | Outcome | Finding and change |
|---|---|---|
| evaluator import smoke | STOP | Python's `tkinter` module existed but `libtk8.6.so` did not; added the runtime package to the evaluator image. |
| Xvfb app launch | STOP | `DISPLAY` was not exported to Tk; entrypoint now sets `DISPLAY=:0`. |
| unauthenticated X11 smoke | construction pass, incomplete capture | Demonstrated capture and key delivery, then exposed that an open X server was too broad; replaced it with per-run MIT-MAGIC-COOKIE authentication. |
| authenticated X11, TCP disabled | STOP | Remote controller could not connect to Xvfb; retained cookie auth and enabled TCP only on the isolated internal network. |
| authenticated X11 readiness probe | STOP | Arena completed while the host-side readiness probe lacked the evaluator's Xauthority; readiness now tests for the actual titled window with the authority set. |
| first report assertion | STOP | Harness expected `spec`/`name`; actual v0 schema uses `episode`/`event`. Assertions were corrected from the source contract. |
| raw capture retrieval | STOP | `/tmp` is tmpfs and is not available after container exit; controller now emits a base64 copy in its captured Docker log, which the harness restores and SHA-256 verifies. |
| `smoke-02` | PASS (construction only) | Authenticated controller captured and retained XWD, sent one `w`, and recorded a natural target-stage deadline miss. Exact artifacts and isolation configuration are beside this ledger. |

The later failures are fixes to the construction harness only. No formal run was started, and no failed construction attempt changes the seed-2001 preregistration.
