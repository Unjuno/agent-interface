# MAP01 attack-onset T9 native startup gate

T9 is a fresh native x86_64 Docker successor to T8's OrbStack linux/amd64
emulation STOP. It uses the same immutable runtime artifact and game entrypoint
to discriminate a host-architecture issue from a general startup failure.

The PR-open/attempt-1 GitHub Actions job runs one candidate on Ubuntu 24.04,
verifies artifact 10398313098 and its full source/wheel manifest, builds the
pinned Python 3.13.5 image, probes only dedicated writable evidence mounts,
then starts real ViZDoom under private Xvfb/Openbox. No retry, gameplay key,
model call, or onset-phase conclusion is allowed. The complete H/T/D/C/U is in
[PLAN.md](PLAN.md); mutation tests and post-experiment local validation are in
[LOCAL_CI.md](LOCAL_CI.md).

The PR is only an execution trigger and evidence carrier. It will not be merged
until the immutable run artifact is downloaded, verified, inspected, and the
actual outcome is added here and to Issue #4223.
