# S17 result — preflight parser still parsed empty output

**FAIL_OR_UNKNOWN (pre-test harness setup).** The second fresh isolated WSLc session again returned exit 0 with empty stdout/stderr from its exact-session, exact-container-name query. The S17 harness source still had an unconditional `JsonDocument.Parse(queryOut)` before the new conditional empty-output handling. It therefore stopped with `JsonReaderException` before image pull, container creation, or unittest execution. This is a second harness setup failure, not a test result.

S17's attempt ID is consumed. The exact session terminated; no container CID was produced, no image was pulled, and the target-generation test did not run. No retry was made. A new successor must remove the unconditional parse entirely and pass a local parser check for empty output before starting any WSLc session.

The 55,574,528-byte isolated VHDX remains at the unique S17 path. Its hash is in `STORAGE-CLEANUP-STATUS.json`; deletion was not retried after the prior command-policy rejection.
