# A04 pre-run STOP — main advanced after freeze

- Frozen base: `9f49b75e72e4dc0596dbfcf2bc7beb7af72652ec`.
- Before either formal command, `git ls-remote origin refs/heads/main` returned `3dba6c86f212c37a2d80c844b816c38921a42cc5`.
- The exact-main gate in `PRE_RUN.md` failed. Candidate invocations: 0. Auditor invocations: 0. Retries: 0. No scientific outcome.
- Inspected range: the three commits add bounded V13 measurement-publication error retention and tests under `research/live_control/executor_v13.py` and its test. No A04 fixture/source path changed; nevertheless the preregistered exact-source gate requires stopping.
- OrbStack preflight STOP was already recorded in `PRE_RUN.md`; it is independent of this main-advance STOP.
- A04 source and this STOP are immutable evidence. Any continuation must use a distinct allocation ID and path, refresh main/source hashes, and append a new preregistration on Issue #5309.
