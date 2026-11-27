# WSL Xvfb cancellation-contract environment recheck

Date: 2026-11-21  
Frozen main HEAD: `3a3cfa18ea5843ed624ca4d590dddb05654e5faf`  
Environment: Ubuntu WSL2, Python 3.12.3, `/usr/bin/Xvfb`, `/usr/bin/xauth`, python-xlib available.  
Runtime/test source: unchanged; exact Git blobs and SHA-256 values are in `conditions.json`.

## Result

The WSL image has `/tmp` mode 1777, but `/tmp/.X11-unix` is mode 0777 and already contains the WSLg `X0` socket. The owned-display tests start Xvfb with TCP disabled. Xvfb reports `Mode of /tmp/.X11-unix should be set to 1777` and cannot bind a usable UNIX listener. The full 41-test X11 supervisor/XRes suite therefore ends with 3 errors in normal mode (5.933 s) and 3 errors under `-O` (10.369 s); each error is an Xvfb private-display startup failure. The same two display-dependent tests fail on an exact frozen source tree extracted to WSL ext4 (2 tests, 2 errors, 1.100 s), so moving the checkout off `/mnt/c` does not resolve it.

A separate fixed-display probe of `Xvfb :99` records the socket-directory mode and Xvfb stderr. The process remains alive but the UNIX socket listener fails. The existing WSLg `X0` socket remains untouched. No WSL permission or socket change was made.

The X-server-independent cancellation/XRes tests pass 34/34 normally (1.626 s) and 34/34 under `-O` (5.969 s) on the same frozen `runtime/` tree extracted to ext4. Full logs retain all errors and passes. Do not interpret the 34-test subset as Xvfb release or live X11 proof.

## Disposition

This attempt is a host-environment HOLD for Xvfb-dependent validation, not a runtime failure or pass. It narrows the blocker to WSL's shared X11 socket-directory state. The current host exposes an active X0 socket; changing the directory mode or disturbing that socket was outside this experiment. Reuse a separately configured private X server host or an authorized isolated environment for the next real-X boundary test. Fake-X late-input evidence remains distinct and still demonstrates the UNKNOWN contract.
