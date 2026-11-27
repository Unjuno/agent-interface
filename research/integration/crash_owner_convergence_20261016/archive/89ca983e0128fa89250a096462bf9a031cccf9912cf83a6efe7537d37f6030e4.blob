# V39/V15 process-owned backend Xvfb test — A03 successor

A02 was a setup STOP before any session child or owner existed because shared
WSL `/tmp/.X11-unix` was not mode 1777. A03 changes only that isolation
boundary: it runs one fresh candidate under an unprivileged user+mount
namespace, mounts a private 64 MiB tmpfs at `/tmp`, and creates a private
1777 X11 socket directory. It leaves the shared X11 directory untouched.
NumPy 2.5.4 is pinned in the user's temporary WSL cache so the private `/tmp`
mount does not hide the dependency.

The hypothesis, candidate treatment, and pass gates remain those in the A02
plan: instantiate the actual opt-in V15 process backend, observe XTEST W
KeyPress and keymap-down, SIGKILL only the session child, then require
independent KeyRelease/keymap-up, the identity-matched fsynced empty release
receipt, stopped owner thread, and owner exit 0 without forced kill. A03 is a
new setup-isolation successor allocation, not a retry or relabel of A02. One
candidate and one raw-only audit are allowed.

Scope remains the actual release-batch backend constructor and raw keyboard
path with a real Xvfb process-death recovery test. It does not run the complete
V15 CLI, image capture, game, model, outer V39 controller, buttons, multiple
keys, physical input, or task-effect measurement. Pillow and the unused GUI
suite remain stubbed only for import; all X11 owner and release code is real.
