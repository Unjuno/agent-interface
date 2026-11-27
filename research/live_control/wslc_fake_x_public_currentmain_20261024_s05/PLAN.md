# WSLc current-main public Fake X characterization S05

Pre-registered 2026-10-24T13:56:28Z, before any S05 WSLc session, image pull or container creation. Source baseline is main commit `2166707229958e095d472c80e160c26449de7a29`; all runtime Python source and the copied probe/auditor/runner/plan are bound by `SOURCE_FREEZE.json` before the run.

**Question:** Can the current public guarded-X11 dispatch characterization execute under the pinned WSLc Python image with the same three Fake X cases and saved-only audit, while the container has no network and source/dependency mounts are read-only?

**Scope:** Fake X memory doubles only. This is a portability/construction check, not a live X server, desktop, physical-input, application, MAP01, task-effect, recovery, efficiency or reliability result. It makes no hard memory-limit claim.

**Frozen route:** one new dedicated `Microsoft.WSL.Containers` API session, unique name and absent storage directory; one host-side pull of `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; one container configured with `NetworkingMode.None`, one CPU, requested 1024 MiB, no GPU/privilege, read-only mounts for current runtime/probe/dependencies, and a unique writable output directory. It runs normal and optimized probe/audit outputs once each from one init process. No Docker, CLI default/shared session, global inventory, retry, or unrelated cleanup.

**Decision:** `PASS_PORTABILITY_SCOPED` only if both interpreter modes exit 0; each saved audit reports `PASS_CHARACTERIZATION_NOT_RELEASE_BOUND`, 26 checks and four rejected mutations; all three cases reconstruct the predeclared healthy/focus-query-block/release-sync-block outcomes; raw hashes and container ID are retained; exact container/image cleanup and dedicated-session termination are recorded; and the exact unique storage path is removed only after successful termination. Any unexpected outcome, timeout, missing receipt, cleanup uncertainty, or nonmatching saved audit is HOLD/UNKNOWN; do not rerun this attempt.

**Known limits:** This repeats the retained public Fake X characterization on current main and WSLc Python 3.12. It does not test cancellation (the probe does not invoke it), any WSLc GUI capability, a safety guardian, physical release, or independent OS/application sensing. The Fake X hypothesis remains falsifiable by changed current-source outcomes.
