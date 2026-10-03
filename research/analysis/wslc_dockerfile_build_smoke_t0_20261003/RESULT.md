# T0 result — PASS, narrowly scoped

The one preregistered WSLc build and the one conditional run both exited 0.

- `wslc build` consumed the exact digest-pinned Python base from cache (`CACHED`), copied the fixed probe and payload, and produced image `sha256:1c325ff52bc0515d073900c048fd1707f2beec00cfdb892ac88ded2defc1a716`.
- The one `wslc run --rm --pull never --network none --cpus 1 --memory 512M` emitted `PASS_WSLc_DOCKERFILE_BUILD_RUN_SMOKE` on Linux/Python 3.12.14. The copied payload was 36 bytes and its SHA-256 matched the frozen source.
- Post-run inventory found the uniquely tagged image and no container with the T0 name. Unrelated existing container rows were not copied into the public package.
- WSLc emitted a warning that cgroup/swap memory limits are unavailable. No memory-cap, peak-RSS, memory-relief, or OOM-prevention claim follows.

This demonstrates only that this minimal local Dockerfile can be built and run through WSLc without a Docker executable in this Windows task environment. It does not compare iteration speed or memory against Docker, establish general Dockerfile parity, cover Compose/Engine API or stronger isolation flags, or establish that any application workflow has migrated. The uniquely tagged test image remains in WSLc's local image inventory; it has not been removed.

The first failed pre-freeze checker was an ad-hoc path-join mistake and is disclosed in [FREEZE.md](FREEZE.md); no WSLc action happened in that failed check. Full command outcome is in [build.output.txt](build.output.txt) and [run.output.txt](run.output.txt); post-run state is summarized in [POSTRUN_CHECK.json](POSTRUN_CHECK.json).
