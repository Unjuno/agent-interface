# Run record

- Classification: posthoc, exploratory, read-only reanalysis; not preregistered.
- Source commit: `b67fc4f33a28f9cea1c4c6cb2d95a470f6be53f3`.
- Candidate: `analyze.py`, invoked once; exit 0; `NO_ZERO_EXPOSURE`.
- Independent audit: `audit.py`, invoked once; exit 0; 5/5 checks passed.
- Added live allocation invocations: 0. Game/controller/model/GUI/input reruns: 0.
- Source artifacts were read via `git show`; no raw source files were modified.
- No container was used: this is a deterministic stdlib-only parser over already-retained telemetry, not a new experiment or runtime test.
- Failures/stops: none. Scope limitation: no zero-ammo observation and no per-window effect event.

See `FREEZE.json` for exact source Git blob IDs and SHA-256 digests, and `SHA256SUMS` for package artifact digests.
