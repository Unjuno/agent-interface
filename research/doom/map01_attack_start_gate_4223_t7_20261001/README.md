# MAP01 attack-onset T7 startup gate

T7 is a fresh successor to T6's output-mount permission STOP. It tests a
scoped output-directory permission repair and then runs the actual ViZDoom
startup candidate locally on OrbStack. It is not the attack-onset experiment.

The immutable offline runtime artifact is 10398313098 with ZIP SHA-256
`522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`. The
candidate builds the pinned Python 3.13.5 Linux/amd64 base, starts
`session_map01_v13.py` at seed 992600 / skill 1 / 60-second timeout under
private Xvfb/Openbox, requires `ready` and the exact initial RGB observation,
and sends only one neutral `finish` command. No gameplay key, model call, or
retry is authorized.

Only the unique candidate and auditor evidence directories are changed to
mode 0777. Each is tested by an isolated container-side write/readback probe
under `--network none`, readonly rootfs, dropped capabilities and bounded
resources before formal candidate/auditor execution. The full H/T/D/C/U is in
[PLAN.md](PLAN.md), and checks are in [LOCAL_CI.md](LOCAL_CI.md).

The T6 hosted-runner permission failure is preserved unchanged. T7's local
OrbStack result is not claimed to reproduce the hosted runner; the container
probe and actual startup result are reported separately with exact environment
and scope limits.
