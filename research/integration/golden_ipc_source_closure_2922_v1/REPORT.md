# Issue #2922 startup-only source-closure preflight

## H — Hypothesis

Providing the historical `research/live_control` and `research/observation_gating`
import roots to the historical `session_v4.py` should allow it to publish one
ready event before task allocation, without changing predecessor source.

## T — Test

- Repository base: historical merged source commit
  `01349d7bc76e5635f5568c53ffeec4d9ff49abb1` (PR #2730), isolated detached
  worktree. The eight runtime source files are enumerated by
  `SOURCE_MANIFEST.json` using Git blob IDs and SHA-256.
- Startup-only allocation: `issue2922-startup-only-seed-992922-20260927-01`;
  seed `992922`; namespace `ready-gate-01`.
- The requested Obstac probe image was tried first. It stopped before route
  import because Pillow (`PIL`) was missing. No package was installed.
- To execute the GUI startup rung, used cached image
  `issue-2849-task1-runtime:v3-20260921`, image ID
  `sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`
  (`linux/arm64`, Python 3.11.2). Source and root were read-only, network was
  disabled, `/tmp` and `/dev/shm` were bounded tmpfs, and no model/provider or
  user desktop was involved. Only `finish` was piped; no task input or submit
  command was sent.
- The wrapper remained at `xvfb-run`/Xvfb for over 30 seconds. `xdpyinfo`
  independently confirmed the X display before one manual USR1 signal was sent
  to release the wrapper. This is an experimental deviation, not a clean run.

## D — Data and disposition

The resulting raw log has four events: one `ready`, one exact initial
observation (`about:blank - Chromium`), the pre-supplied `finish`, and an
evaluator result indicating missing task output. There were zero submit
commands, input-admission events, or model calls. The fixture endpoint was
constructed at `http://127.0.0.1:36765/`, but Chromium did not request it.
Screenshot `001.png` is the retained `about:blank` observation. The container
exit code was not captured because the short-lived `--rm` run was not attached
to a retained command session.

**Disposition: `HOLD_XVFB_READY_SIGNAL_INTERVENTION`.** The import roots enabled
startup to reach `ready` after intervention, but the wrapper required manual
release, the fixture page was not reached, and there is no task effect. This
does not satisfy Issue #2922's route closure claim and is not a task PASS.

An independent raw-only audit reports no integrity errors across the four raw
events and eight source files. Six audit tests pass (one baseline and five
corruption controls for ready identity, endpoint, submit, source digest, and
input event).
The first audit implementation had a manifest path-prefix bug; it was fixed,
then the full six-test suite passed. That was an auditor development defect,
not experimental evidence.

## C — Constraints

This is a private synthetic Linux/arm64 GUI startup check against cached
historical sources and a separate cached GUI runtime. The explicitly requested
Obstac image lacked a required dependency. The USR1 intervention invalidates a
clean readiness claim. No task action, application effect, live user desktop,
production route, network behavior, or equivalence between images was tested.

## U — Uncertainty and next rung

Do not reuse seed `992922` or namespace `ready-gate-01`. The next safe
experiment needs a pinned runtime containing the required imports and a
non-intervened Xvfb readiness handshake; then independently verify the fixture
request before considering any task allocation. Preserve this preflight and
its HOLD result as immutable predecessor evidence.
