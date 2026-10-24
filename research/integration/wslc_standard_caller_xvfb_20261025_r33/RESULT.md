# R33 — pre-container stop: Docker Desktop WSL mount service unavailable

**Disposition: STOP_PREINPUT, no container created.** The exact pinned Ubuntu image was present after digest-pinned download. The `docker run` invocation then failed with exit 127 before container creation because Docker Desktop could not resolve the WSL UNC XKB mount (`/run/guest-services/distro-services/ubuntu.sock` absent). An exact-name inspect/log check confirmed no R33 container existed. The public caller and Xvfb did not start; input count is zero.

This is an orchestration mount setup failure only. R33 is not retried. R34 stages the XKB data through a repository-local, hash-pinned read-only bind mount instead of the unavailable WSL UNC mount. The fixed image remains the same digest and the trial remains network-isolated.
