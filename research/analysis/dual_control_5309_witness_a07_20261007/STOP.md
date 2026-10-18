# A07 pre-start STOP — output mount source path typo

- Frozen allocation: `5309-WITNESS-A07-ORBSTACK-20261007`, main `3dba6c86f212c37a2d80c844b816c38921a42cc5`, pinned Python image as recorded in `PRE_RUN.md`.
- The one preregistered formal candidate `docker run` attempt failed before container creation because the `out/` bind source was mistyped (`agent-interface-5309-witness_a07_20261007/out`); Docker reported source path not found, exit 125.
- Candidate process invocations 0; raw absent; auditor invocations 0; retries 0; no scientific outcome.
- Candidate/auditor mount-isolation construction smokes and host tests passed, but they do not convert this formal launcher STOP into an experiment.
- No existing container was modified or removed. A04–A07 are immutable and not rerun.
