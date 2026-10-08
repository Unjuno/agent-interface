# Excluded construction01

One preformal CLEAR smoke ran in the pinned image (ID `sha256:acf83a1dfafd43c44d81e2f28f85fc844fa43dc73f36b689a862dd924f9235d0`) with network disabled, read-only root/source, 1 CPU, 1 GiB, 64 PIDs, private authenticated Xvfb :239, TCP disabled. It is not one of the 12 formal sessions and is never pooled.

- Runner status: COMPLETE; Xauth exit 0; parent MapState 2; VisibilityNotify [0]; exact assessor result CLEAR_PARENT_REGION_SCOPED; no children.
- Both source frames returned 38,400 bytes with the same SHA-256 `521c39d6d0a330a908c62f23cd93d99403034bfea7cfa2777379d55bbeb10a88`.
- Xvfb exited 0; X socket and auth file were absent after cleanup.
- Construction JSON SHA-256 `6efdbc8952d8e2029bed2b474840f4611dd74ddf19ac810e1a843a4497a2bd4a`.
- Raw bytes and execution log are retained locally under the task workspace's `run-output/construction01/`; later publication uses base64 wrappers with the original 38,400-byte length and hash. Formal gates do not depend on this smoke.

The smoke is wiring/readiness evidence only, not a scientific outcome.
