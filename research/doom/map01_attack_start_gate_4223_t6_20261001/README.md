# MAP01 attack-onset T6 startup gate

This package is an actual-game technical gate for Issue #4223, not a test of
the two attack-onset arms. It gives the next fresh allocation a measured
answer to the prerequisite left open by allocation 04: can the real
ViZDoom process initialize through Xvfb/Openbox, emit its first exact
observation, and report its process exit status?

The candidate uses the immutable offline source/wheel artifact 10398313098,
constructs a Linux/amd64 Docker image from a digest-pinned Python base, starts
`session_map01_v13.py` at seed 992600 / skill 1 / 60 s episode timeout, and
sends only one neutral `finish` after `ready` and the first observation. No
gameplay key, attack, model, or task-effect claim is involved.

The workflow is deliberately PR-open-only and attempt-1-only. Its upload
retains image-build logs, container commands/IDs, the full runtime source,
child stdout/stderr, Xvfb/Openbox logs, exact PNG, raw JSON and independent
audit. A green workflow is not itself the scientific result; use `REPORT.md`
and the uploaded immutable artifact. If main drift touches the relevant
research scope or any one-shot prerequisite fails, preserve the resulting
STOP and do not rerun this allocation.

Local source/audit mutation checks are in [LOCAL_CI.md](LOCAL_CI.md). The
prespecified hypothesis, outcome gates, constraints and limits are in
[PLAN.md](PLAN.md). Allocation 04's historical STOP remains untouched.
