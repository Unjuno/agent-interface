# S16 result — exact-name preflight parser stopped before test

**FAIL_OR_UNKNOWN (pre-test harness setup).** One new isolated WSLc 3.0.3.0 session started at the preregistered unique storage path. Its exact-session, exact-container-name query exited 0 and returned empty stdout/stderr, indicating no row in that scoped query. The harness incorrectly required JSON `[]`, threw `JsonReaderException`, and stopped before image pull, container creation, or unittest execution. This is a harness contract failure; it is not a Fake X test result and does not count as a computer-control pass.

The session termination receipt is true. No container CID was issued, no image was pulled, and no test raw directory or result file was produced. This attempt ID is consumed and was not retried. S17 uses a distinct attempt and corrects only the preflight parser to accept the observed empty-output representation for a successful exact-name filter.

The 55,574,528-byte isolated session VHDX remains at the unique recorded storage path. Its size and SHA-256 are recorded in `STORAGE-CLEANUP-STATUS.json`. The same exact-file deletion was rejected by command policy in earlier cleanup attempts, so it was not retried here.
