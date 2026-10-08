# T7 execution report — STOP before candidate

## Outcome

**STOP_IMAGE_BUILD_INVALID_PACKAGE_NAME**. Runtime artifact verification
passed (2,592/2,592 source files and 12/12 wheels), but the pinned Linux/amd64
image build stopped before either output-mount probe or formal candidate.
`Dockerfile` requested Debian package `libxext7`, which does not exist in the
frozen Bookworm repositories; the correct package name is `libxext6`.

This was a T6-to-T7 mechanical-copy typo (`libxext6` was changed while
replacing the allocation suffix). Candidate invocations: 0; auditor
invocations: 0; retries: 0. No DoomGame process was started. This is not a
result about the T7 output-permission hypothesis or ViZDoom startup.

## Frozen run

- Allocation: `MAP01-ATTACK-ONSET-STARTGATE-4223-T7-20261001-01`
- Source commit: `e0edeec3063079d0cb2ba67e9ba42592c7b98b75`
- Engine: local OrbStack, Docker Engine 29.4.0, host arm64, target linux/amd64.
- Runtime artifact: ID 10398313098, ZIP SHA-256
  `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`.
- Verified closure: 2,592 runtime source files and 12 wheels.
- Exact build command and image-build log are in `OBSTAC_EXECUTION.json` and
  `docker-build.log` in the local run output; the package failure is also
  captured in the T7 execution notes on Issue #4223.

The consumed T7 freeze remains unchanged. Any candidate requires a new
successor allocation with the corrected dependency list; no T7 rerun is
authorized or performed.
