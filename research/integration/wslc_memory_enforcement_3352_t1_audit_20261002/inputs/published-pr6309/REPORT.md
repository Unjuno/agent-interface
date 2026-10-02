# WSLc memory-cap enforcement probe — 2026-10-02

## H/T/D/C/U and disposition

- **H:** `wslc run --memory 128M` enforces an effective 128 MiB resident-memory ceiling; a 384 MiB allocation fails, while the 512 MiB positive control completes it.
- **T:** Run the same saved read-only Python probe twice, each in a fresh WSLc container with pinned image digest, `--pull never --network none --cpus 1`, changing only `--memory` (512M control, 128M constrained). Probe reports `/proc/self/cgroup`, `/sys/fs/cgroup/memory.max`, touches one byte per 4 KiB over the allocation and holds 1 second.
- **D:** **FAIL (scoped)**. Both runs exited 0 and printed `ALLOCATED_MIB=384`. The 128M run reported `memory.max=134217728`; control reported `536870912`. Thus reported cgroup limit does not establish effective enforcement in this environment.
- **C:** WSL package 3.0.1.0, `wslc` 3.0.1, Ubuntu 24.04.4 LTS on WSL2, kernel 6.18.40.1-microsoft-standard-WSL2. Image `python:3.12-slim`, immutable repo digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`). Source SHA-256 `FCC6AF165725F7654EB15541A8F9014B233308DB595D897325B1B758345B1D47`. Exact command arguments are in `commands.txt`; outputs in `raw.log`.
- **U:** Synthetic allocation only, not a representative roadmap application. WSLc warned: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” `/proc/self/cgroup` was `0::/`; cgroup2 and `memory.max` were visible. No swap limit, host peak-memory measurement, Docker comparison, throughput/iteration-time comparison, or memory-pressure experiment is established. The positive control validates probe execution only, not performance parity. Do not rely on WSLc `--memory` as a safety/resource guarantee on this host pending a successor test on a cgroup-enforcement-capable environment.

## Independent audit

The raw output matches the declared decision rule: constrained and control arms both successfully touched and retained 384 MiB; requested memory.max values match configured limits. This falsifies H for this environment. This is a self-audit, not an independent reviewer; independent audit and merge gate remain open. The issue also requires a representative roadmap experiment before closure, so this record alone does not satisfy #3352's closure condition.

## Reproduction

See [probe.py](probe.py), [commands.txt](commands.txt), and [raw.log](raw.log). Source hash: `FCC6AF165725F7654EB15541A8F9014B233308DB595D897325B1B758345B1D47`.
