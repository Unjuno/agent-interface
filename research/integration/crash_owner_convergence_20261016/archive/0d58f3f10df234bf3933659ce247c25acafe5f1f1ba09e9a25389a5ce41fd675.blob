# V39/V15 process-owned backend Xvfb test — A02

## Hypothesis

The actual opt-in V15 `Backend` class can admit a held key through its
`InputOwnerProcess`; if only its session process is SIGKILLed, the separate
owner process retains the private X connection, releases the key through its
normal close path, writes a verified fsynced receipt, and exits without being
forced down.

## Frozen setup and treatment

- One private `Xvfb -displayfd` server, TCP disabled, with an independently
  selected focus window and two observer connections for XTEST event/keymap
  verification.
- One session child instantiates
  `doom_owner_thread_release_batch_backend_process_v1.Backend` from the frozen
  source graph, binds a 25-second focus-bound lease, and holds the allowlisted
  `w` key through the backend's production `raw()` method.
- After an independent KeyPress event and XQueryKeymap-down sample, the
  supervisor sends SIGKILL only to the session child. It is a Linux subreaper
  and keeps Xvfb alive while observing the owner process and independent
  KeyRelease/keymap-up.
- The owner must write an identity-matched fsynced receipt, report empty
  verified key/button state and stopped owner thread, and exit 0. Forced owner
  termination, missing evidence, or a gate timeout fails this rung. Xvfb is
  then terminated by the supervisor.
- A one-shot candidate and one raw-only audit are allowed; no retry or live
  game/model allocation is included.

## Scope

This tests the actual release-batch backend constructor and keyboard input
method, real InputOwner V4/V3/V12 service, framed local adapter, process death,
XTEST server state, and independent X event observation. It does not execute
the full V15 CLI, image capture, ViZDoom, the planner, outer controller
failure-report writer, buttons, multiple held keys, physical devices, or task
effect. Pillow and the unused `gui_suite` are stubbed only to make the backend
module importable without invoking capture or app selection. NumPy is installed
in a temporary WSL `/tmp` target and is pinned in the run record; no system
package is changed.
