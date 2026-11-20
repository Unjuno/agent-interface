# Full child-stdin pipe blocks controller failure cleanup

## H/T/D/C/U

- **H:** On current main `8bcf6711cd24afe230236e54cb8a27987ecc092f`, filling the owned child's stdin pipe while the child ignores stdin blocks the synchronous `finish` write/flush. The cleanup context therefore cannot reach its timed wait or planner close until the child is externally released.
- **T:** Freeze the literal `doom_controller_failure_cleanup_v1.py` blob from that main revision and run one CPU-only WSLc construction using a real Python child. Fill its stdin to nonblocking `EAGAIN`, restore blocking mode, trigger cleanup in a worker thread, observe for 0.5 seconds, then kill only the owned child as separate probe cleanup and join the worker. Record cleanup progress before external release separately from post-release completion.
- **D:** Pending the one frozen run and an independent raw-result audit.
- **C:** A synthetic full pipe establishes this exact blocking boundary, not a real model/game/input failure or a general cleanup deadline.
- **U:** A controller-origin cleanup path blocked on a kernel pipe can still be repaired without changes to shared processes or services. Process exit does not prove physical input release.

## Frozen construction

- Source: exact main commit `8bcf6711cd24afe230236e54cb8a27987ecc092f`, cleanup helper copied byte-for-byte into `source/`.
- Workload: one child, ignores stdin, parent fills the pipe to `EAGAIN`; one cleanup attempt; one 0.5 s barrier; external kill is allowed only after barrier observation.
- Runtime: cached WSLc image `sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378`, network disabled, user 65534, one CPU, 512 MiB requested. The container has no game, model, GPU or GUI.
- Expected discriminator: blocked cleanup thread, child still alive, and planner still open at the barrier. External kill and subsequent thread completion are separate evidence.

Construction setup attempt 01 exited before importing the probe because its WSLc command omitted the probe-script mount. Its command and raw stdout/stderr are retained in `setup-failure-01/`; it started no child and is not a baseline result. The corrected single probe invocation writes to `baseline-run-02/`.

This package is a construction boundary probe. It does not replay a game allocation or establish input release, scorer completion, or a universal timeout.
