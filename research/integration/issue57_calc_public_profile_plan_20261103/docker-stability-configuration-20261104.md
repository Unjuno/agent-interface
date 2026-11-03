# Docker Desktop stability configuration record — 2026-11-04

## Active configuration

The host uses Docker Desktop's WSL 2 backend. The current
`C:\Users\user\.wslconfig` contains:

```ini
[wsl2]
memory=32GB
processors=12
swap=16GB

[experimental]
autoMemoryReclaim=gradual
```

The host has 64 GB physical RAM and 24 logical CPUs. This profile caps WSL at
32 GB and 12 CPUs, leaving half the host RAM and CPUs for Windows and other
work. Gradual memory reclamation remains enabled. Docker Desktop Resource Saver
is disabled and auto-start is enabled. Resource Saver stays disabled to avoid
intentional idle suspension. Previous WSL limits were 24 GB, 8 CPUs and 8 GB
swap; the original file is backed up at
`C:\Users\user\.wslconfig.before-docker-stability-20261104`.

Docker Desktop was stopped, WSL shut down to apply `.wslconfig`, then Docker
Desktop was started. Memory, CPU and swap were changed together as one bounded
profile; this does not isolate the effect of any single setting.

## Current engine check

- Docker Desktop status: `running`.
- Engine: 29.8.1; Docker Desktop reports 12 CPUs and 33,658,011,648 bytes of
  engine memory.
- Containers: 0 running after the test.
- Earlier broad composed run: cached image pinned by digest, network disabled,
  2 CPUs, 4 GiB memory and 4 GiB total memory+swap, 256 PID limit, source
  read-only, exit 0; normal and optimized suites each passed 214/214 before the
  current validator change.
- Current reuse-horizon attempt-accounting run: same image and isolation
  limits; normal and optimized modes each passed 14/14, exit 0. Logs and
  checksums are retained in
  `reuse-horizon-attempt-accounting-20261104-01/`.
- The four previous broad-run packet manifests and the current validator packet
  manifest verify. `git diff --check` passed.

A bounded test run establishes that Docker remained responsive through that
run, not a long-duration stability rate or the cause of earlier crashes. Recent
Docker host logs did not show an OOM or backend panic; they did show skipped
bind-mount warnings during prior container launches. The cause of the earlier
Desktop crash remains unverified. No Docker Desktop upgrade was performed.

## Next stability evidence

For a causal stability comparison, capture Docker Desktop diagnostics and
Windows event logs around a reproducible crash, then compare this profile with
the preserved prior limits under the same workload. Record engine restarts,
container exits, OOM events, host memory pressure and duration. This
configuration is stability-oriented; evidence that it fixed the crash is not
yet available.