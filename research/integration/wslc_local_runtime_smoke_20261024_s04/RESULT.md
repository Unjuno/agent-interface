# Result S04

**Runtime subcriteria: PASS. Overall attempt: HOLD — two audit/cleanup issues remain.**

The official WSLc API reported all prerequisites present, created the unique session, pulled the pinned image, and ran one container configured with networking `None` and a read-only source mount. The Python process exited 0. Its raw JSON parses as probe `PASS`, matching the preregistered sentinel SHA-256, with a rejected write (`EROFS`). The full container ID was captured. The exact container and image were deleted, and the dedicated session terminated.

The .NET harness returned exit code 1 because its final check searched for the compact substring `"probe":"PASS"`, while the emitted JSON contains whitespace (`"probe": "PASS"`). The raw process output independently parses and satisfies the frozen marker, hash, EROFS, and container exit criteria. No second container run was made.

The dedicated session leaves a 203,423,744-byte `storage.vhdx` at the exact unique path recorded in `run/storage-retained.json`. The execution policy rejected the command to delete this generated VHDX before the command ran, so the frozen storage-removal criterion is unmet and the overall attempt remains HOLD. The runtime/API behavior still provides qualified evidence for session start, pinned-image pull, network-disabled execution, read-only-mount rejection, exact container/image cleanup, and session termination.

This does not test Windows GUI input, input release, environment response, bounded recovery, or task effect. It does not prove hard enforcement of session resource settings or repeatability.
