# Issue #2922 — historical route source-closure preflight

This additive package records a single setup-only historical-route startup
probe. It is a bounded diagnostic, not a task allocation or efficacy result.
The immutable source snapshot is commit
`01349d7bc76e5635f5568c53ffeec4d9ff49abb1` (merged PR #2730); the current-main
intake was `b63e6ee0d6cfc20a0964fb73cc476ba0709fd876`.

## Disposition

`HOLD_XVFB_READY_SIGNAL_INTERVENTION`.

`session_v4.py` imported and emitted `ready` after the historical source tree
was mounted read-only with both `research/live_control` and
`research/observation_gating` on `PYTHONPATH`. The container's `xvfb-run`
waited indefinitely for Xvfb's `SIGUSR1` readiness notification even though
an independent `xdpyinfo` call proved display `:99` responsive. One explicit
signal was then sent to let this setup-only process continue. Chromium opened
`about:blank`; no `submit`, model call, or task input was sent. The independent
evaluator returned false because the task output file was correctly absent.

This is evidence that the historical import/startup path can reach its
`ready` event under this amended container setup. It is **not** a clean
preflight PASS: the out-of-band X-server signal is a harness intervention,
the configured local fixture endpoint was not requested by Chromium, and no
task effect was tested. The original Issue #2922 STOP and all predecessor
artifacts remain unchanged.

A later, separate no-GUI import-only rung passed in the same pinned historical
GUI runtime image, with no Xvfb or Chromium invocation. See
[`NO_GUI_IMPORT.md`](NO_GUI_IMPORT.md) and `NO_GUI_IMPORT_RESULT.json`. This
narrows uncertainty about Python import closure only; it does not upgrade the
earlier startup HOLD or establish runtime readiness.

## H / T / D / C / U

- **H** — Supplying the retained route's transitive import roots will allow
  its session entry point to import and publish a `ready` event before any
  task command is issued.
- **T** — One fresh startup-only instance, seed `992922`, historical source
  commit `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`, read-only source mount,
  `--network none`, pinned cached image
  `issue-2849-task1-runtime:v3-20260921` (`sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`),
  Python 3.11.2, private Xvfb/Openbox/Chromium. After the initial wrapper
  stalled, display responsiveness was independently checked and one
  `SIGUSR1` was sent to the wrapper; only `{"op":"finish"}` was supplied.
- **D** — `ready` was emitted once; the initial observation was exact and
  showed the expected `about:blank` startup page; the only command was
  `finish`; no submit/input event occurred. Overall disposition remains
  `HOLD_XVFB_READY_SIGNAL_INTERVENTION`, not PASS, because the readiness signal
  required intervention and no fixture request/task effect was observed.
- **C** — Private synthetic Chromium/Xvfb only; network disabled; source and
  root filesystem read-only; no model/provider, user desktop, physical input,
  or consequential task action. A separate attempted import in cached
  `issue-3300-obstac-probe:v1` stopped at missing Pillow (`ModuleNotFoundError:
  PIL`); that image is not represented as a GUI runtime and its STOP is kept
  separate.
- **U** — No independent proof that the historical task route reaches its
  intended fixture page, produces an application effect, or has complete
  source closure in the original runner image. No task success, runtime
  reliability, or cross-image equivalence is claimed.

## Retained evidence

- `events.jsonl`, `sources.json`, and `setup-diagnostics.txt` are copied from
  the writable evidence bind mount.
- `SOURCE_MANIFEST.json` binds eight runtime files to Git blob IDs and SHA-256
  digests in the historical source tree.
- `environment.json` records both container images, platform, and runtime
  limits.
- `source_snapshot/` retains all eight hash-pinned historical source files.
- `audit.py` recomputes source identities and checks the raw event and separate
  no-GUI import-only result contracts without importing the runner;
  `test_audit.py` includes the startup and direct-Xvfb raw bundles, five
  historical-event mutation controls, and contract checks for the two later
  import/readiness rungs. A separate host-only AST-extracted GET-handler probe
  records the fixture response without output mutation; it is explicitly not
  containerized or an integrated-session result.
- `001.png` is the retained first observation (Chromium `about:blank`), not a
  task-effect image.

The setup-only seed `992922` and output namespace
`ready-gate-01` are consumed and must not be reused as a later task allocation.
