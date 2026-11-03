# Docker Desktop stability configuration record — 2026-11-04

## Active configuration

The host currently uses Docker Desktop's WSL 2 backend. The verified
`C:\Users\user\.wslconfig` contains:

```ini
[wsl2]
memory=24GB
processors=8
swap=8GB

[experimental]
autoMemoryReclaim=gradual
```

In Docker Desktop, WSL 2 is selected, Resource Saver is disabled, and
Docker Desktop is configured to start on login. Disabling Resource Saver keeps
the engine from being intentionally suspended during idle periods. Gradual
memory reclamation returns unused guest memory progressively. The WSL VM is
bounded to 24 GB RAM and 8 CPUs with 8 GB swap so it cannot consume all host
resources. These values were already active; this task verified and documented
them without changing the host configuration.

## Current engine check

- Docker Desktop status: `running`.
- Engine: 29.8.1; Docker Desktop reports 8 CPUs and 25,203,236,864 bytes of
  engine memory.
- Containers: 0 running at the post-test check.
- Recent isolated integration run: cached image pinned by digest, network
  disabled, 2 CPUs, 4 GiB memory and 4 GiB total memory+swap, 256 PID limit,
  read-only source mount, container exit 0; normal and optimized suites each
  passed 214/214.
- Four run packets' SHA-256 manifests verified; `git diff --check` passed.

The test container limits and host WSL allocation are separate controls. A
single bounded test run establishes that Docker remained responsive through
that run, not a long-duration stability rate or cause for earlier crashes.
No Docker Desktop upgrade or host restart was performed. A newer Desktop
version had previously been offered, but its installer required elevation and
was not applied.

## Next stability evidence

For a causal stability comparison, capture Docker Desktop diagnostics and
Windows event logs around a reproducible crash, then vary one resource setting
at a time under the same workload. Record engine restarts, container exits,
OOM events, host memory pressure, and duration. Avoid changing RAM, CPU, swap,
Resource Saver, and workload simultaneously because that would confound the
result.
