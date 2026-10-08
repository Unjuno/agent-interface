# Allocation 01 pre-stage infrastructure STOP

On 2026-10-03 at approximately 09:02 UTC, runner.py stage returned exit 1 at
`orbctl run -m research-6183-t0-20261003 docker ps -a --format '{{.Names}}'`.
The direct diagnostic stderr was:

```
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

The Docker service was active (Docker 29.1.3), but guest user taka UID/GID 501
does not belong to its socket group. This was not a daemon-start delay. The
default context points at the private VM socket, not the shared OrbStack engine.

No staging directories had been created, no docker run occurred, no candidate,
legacy diagnostic or auditor process started, and no formal output exists.
Formal invocation counts: candidate 0, legacy diagnostic 0, auditor 0.
The original source/hash freeze is preserved in FREEZE.json and its Git commit.
Do not change socket/group policy or retry this runner unchanged.

A prospective command-only revision will use explicit guest root solely for
Docker administration on this owned private VM, retaining UID/GID 501:501 inside
all containers and ordinary taka ownership for staging/output directories. That
revision needs separate allocation/path identity and FREEZE_02.json before run.
Candidate, fixture, independent oracle, legacy probe and decision gates do not
need scientific changes. Historical #6183 outputs/containers remain untouched.
