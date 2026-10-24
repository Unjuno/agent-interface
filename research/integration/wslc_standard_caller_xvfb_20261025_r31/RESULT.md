# R31 — pre-input stop: WSL X11 socket directory mode

**Disposition: STOP_PREINPUT, zero test input.** The registered 3,250 ms public-caller test never started. The local Xvfb child did not create its private `:88` socket, and the runner stopped before XRes preflight or any caller action. This is an environment/setup failure, not a release, task-effect, or reliability result.

Xvfb retained the exact diagnostic: `_XSERVTransmkdir: Mode of /tmp/.X11-unix should be set to 1777`, followed by failure to bind the UNIX listener. A read-only post-run check found `/tmp/.X11-unix` at mode `0777` (owner root), with the preexisting WSLg `X0` socket still present and `X88` absent. The child Xvfb process exited and the runner recorded exact-process cleanup. No display permission was changed by R31.

The preregistered rule forbids retrying R31. A distinct R32 may proceed only with the missing sticky bit recorded as a changed setup condition and a fresh attempt ID. R31 raw output, runner, hashes, and preregistration remain preserved.

## Scope

No Xlib/XRes identity preflight, input injection, release, readback, task oracle, or late-event horizon occurred. This packet contributes only a diagnosis of the local WSL Xvfb setup. It says nothing about WSLc-container behavior, MAP01, Win32, or computer-control correctness.
