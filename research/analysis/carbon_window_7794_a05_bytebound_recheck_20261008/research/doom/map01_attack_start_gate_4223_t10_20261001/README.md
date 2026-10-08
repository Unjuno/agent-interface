# MAP01 attack-onset T10 native startup gate

T10 tests whether adding and preflighting the `wmctrl` executable omitted in
T9 allows the same pinned runtime to progress past its observed pre-ready stop.
It is a fresh native x86_64 GitHub-hosted Docker allocation, not a local
OrbStack run or a rerun of T9. The one-shot candidate, scope and decision gates
are preregistered in [PLAN.md](PLAN.md).

The PR-open/attempt-1 job verifies immutable runtime artifact 10398313098,
builds the pinned Python 3.13.5 image, and requires `wmctrl` during image build
before it can invoke the real game once. It uses isolated output-mount probes,
private Xvfb/Openbox, no network, and no gameplay input or model calls. An
independent auditor runs only if the candidate exits zero. Local checks are in
[LOCAL_CI.md](LOCAL_CI.md); they are not experimental evidence.

The PR is only an execution trigger and evidence carrier. It will not be merged
until the immutable workflow artifact and exact outcome are inspected, retained
here and reported on Issue #4223.
