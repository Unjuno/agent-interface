# R34 — pre-Xvfb stop: staged Python runtime loader path

**Disposition: STOP_PREINPUT, no Xvfb or test input.** The exact pinned-image container was created with network disabled and the intended read-only mounts, but its initial Python process exited 127 before running the test runner. The loader reported that `libexpat.so.1` was unavailable because the parent process did not receive `LD_LIBRARY_PATH=/tmp/stage/lib` and `PYTHONHOME=/tmp/stage`.

The original R30 launcher record shows the missing setup: it copies the read-only stage into tmpfs, sets executable bits, places the staged `xkbcomp` in `/usr/bin`, and starts Python with both environment variables. The stopped R34 container was removed by its exact unique name and verified absent. No Xvfb process, test body, or synthetic input was started. R34 is not retried; R35 preregisters the corrected initialization path with an ephemeral writable container root and read-only host mounts.
