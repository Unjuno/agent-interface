# Preserved preflight stop — container-local package build

This did not reach the formal MCP fixture call. Attempted to run
`runtime/distribution_v2/build.py` inside the runtime image with the checkout
mounted read-only and network disabled. The builder requires `git` to resolve
committed `HEAD`; the runtime image does not contain Git, so it exited before
writing the artifact (`FileNotFoundError: [Errno 2] No such file or directory:
'git'`, wrapped as `RuntimeError: cannot pin committed build source`).

No MCP client/server, GUI fixture, Xvfb, or dispatch was started by that attempt.
The formal package is therefore built outside the runtime image from the exact
committed source revision recorded in `manifest.json`; runtime remains isolated.
