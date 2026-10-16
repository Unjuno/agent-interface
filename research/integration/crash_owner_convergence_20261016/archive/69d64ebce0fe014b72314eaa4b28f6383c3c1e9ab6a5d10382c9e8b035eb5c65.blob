# V39/V15 process-owned backend Xvfb test — A04 successor

A02 and A03 are retained setup STOPs: A02 could not create an X11 socket in
the shared `/tmp`; A03 failed before Xvfb because its result leaf was
pre-created. A04 carries forward the A03 private tmpfs/mode-1777 X11 socket
boundary and corrects output ownership by leaving `results/A01` absent for the
candidate's exclusive `mkdir(exist_ok=False)`. It does not touch either prior
result package.

The hypothesis and gates remain unchanged: instantiate the actual opt-in V15
process backend, observe XTEST W KeyPress and keymap-down, SIGKILL only the
session child, then require independent KeyRelease/keymap-up, an
identity-matched fsynced empty release receipt, stopped owner thread, and
owner exit 0 without forced kill. One candidate and one raw-only audit are
allowed; this is a new setup successor, not a retry or relabel.

Scope remains an Xvfb process-recovery boundary for the actual release-batch
backend constructor/raw keyboard path. It does not run the complete V15 CLI,
image capture, game, model, outer V39 controller, buttons, multiple keys,
physical devices, or task-effect measurement. Pillow and the unused GUI suite
are stubbed only for import. NumPy 2.5.4 is pinned under the user's temporary
WSL cache; X11 owner and release code is real.
