# DOOM transfer to the shared runtime

The new `session_v6.py` uses the same `session_v8` backend and `executor_v3`
as `interactive_v10.py`: absolute intent deadlines, independent input owner,
observed focus binding, read-only recovery and full observation delivery.
The pinned reference manifest is checked before startup and archived with the
adapter hash. It is a reference inventory (including the unused GUI entrypoint),
not a claim that every listed file is executed by DOOM. Core runtime files are
unchanged. The legacy DOOM entrypoints and their results remain intact.

DOOM-specific setup retains ASYNC_SPECTATOR, Freedoom assets, a visible private
Xvfb window, XTEST key input and a nominal 35-tic clock. Engine telemetry refresh
calls occur outside the two-second clock wait and after control for scoring;
the controller never uses engine action selection. Clock measurement includes
the final refresh overhead, so it is a coarse readiness check.

## Recorded development and fresh verification

| Cohort | Sources | Outcome |
|---|---|---|
| shared-readiness-01 | session_v5 + shared_readiness | 3 failures before ready was consumed: Xlib input-owner connection diagnostics contaminated JSON stdout. Runtime remained alive until the harness closed stdin; the harness error text incorrectly says runtime exited. Original non-JSON line was not archived; the next revision's backend-setup.txt identifies the Xauthority warning. |
| shared-readiness-02 | session_v6 + shared_readiness_v2 | 3 failures: valid hold requests used obsolete key/ms fields instead of keys/duration_ms. Runtime rejected them before input; the harness waited for terminal and timed out. |
| shared-readiness-03 | session_v6 + shared_readiness_v3 | 3 readiness passes: ordinary hold, cancellation after input admission, and expiry during a hold. Every case also rejects an already-expired request and accepts a separate fresh observation afterward. |

Revision 6 redirects backend initialization diagnostics before executor startup.
Harness v3 uses the existing command schema and reports unexpected rejection
immediately. Both failed harness revisions remain frozen with source hashes.
These are adapter/harness defects, not new proven core failure classes.

The passing cohort has **10 exactly reconstructed image frames**, six terminal
program records with verified release, full raw/delivered event equality and
verified owner shutdown in all cases. Interrupted tails were never started and
only the intended Right key was admitted. Expiry had input admission before its
deadline; cancellation was matched after admission. This is not an independent
external key-state monitor or a broad wrong-target/stress qualification study.

Measured coarse clock rates: ordinary 34.979, cancel 35.036, expiry 35.017 tic/s.
All three post-control scores report unfinished episodes and living players.
**No game success, model speed, token savings or human-tempo claim is made.**
This cohort is scripted input readiness, not assistant gameplay. It does not
qualify a freeze revision. A common-runtime assistant self-use episode, focus
transfer/critical-event tests and the continuous tracking adapter remain open.

## Reproduce and audit

Use the ViZDoom Python environment with X11/Pillow and existing suite dependencies:

```sh
python research/doom/shared_readiness_v3.py --out <new-unique-directory>
python research/doom/audit_shared.py <new-unique-directory>
```

The manifest fixes cases, source hashes and clock gates before execution. Game
assets/version/mode are recorded per run; full OS/dependency environment versions
are not preregistered, so this is not yet the complete qualification manifest.
The auditor verifies source bytes, image transport against saved PNGs, stale
rejection, interruption ordering, release/close and retained tails from raw logs.
Its success does not replace the missing full qualification study.

## Actual shared self-use update

[Shared self-use report](SHARED_SELF_USE.md) records an unsuccessful assistant
episode: black output after the first planner gap, retained despite frame/cleanup
audits passing. A fresh 0/20-second scripted pair did not reproduce black output,
but showed no world-crop change after its short turn. Game response and rendering
freshness are unresolved; readiness does not prove useful feedback.
