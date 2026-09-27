# Issue #3631 — representation-bound proxy effect unit

An additive fresh successor to the #3619 HOLD and #3626 scoped PASS. The one-shot formal allocation evaluates source-XID-to-live-process identity, arm-specific derivation from assigned representations, and canonical output-path enforcement, retaining the existing ambiguity, no-effect, and release controls. Historical evidence is untouched.

See `PREREGISTRATION.md` for H/T/D/C/U and frozen decision gates; `PRECHECKS.md` for construction dispositions; `REPORT.md` and `evidence/formal-04/` for the final result. No generic virtual-GUI platform or runtime promotion is included.

The Issue #3631 acceptance matrix is preregistered as H/T/D/C/U in `PREREGISTRATION.md`. We checked the issue and parallel work against main through `600dabef6bdc071214eb2fbad80411cc271fc0d5`; this dedicated directory is collision-free. The local pinned image is OrbStack `linux/arm64`; no Docker Desktop fallback is used.

Construction gates run separately and may be corrected before freeze. `formal_launch.sh` enforces the exact `evidence/formal-04` and `evidence/preflight-04` paths, rejects symlink aliases, validates all frozen hashes, runs unit tests and the Xvfb/XRes/screenshot smoke, then invokes the 28-row formal runner exactly once. The formal container has network disabled, read-only root/source, and a fresh evidence mount. After invocation, no retry or replacement run is allowed.
