# Successor #4908 v4 — launcher/output-boundary construction rung

## H / T / D / C / U

### H
Separating host launcher logs/receipt from the runner's initially empty `/out` directory prevents the v2 pre-fit output-not-empty STOP while retaining the runner's fail-closed empty-output precondition.

### T
Fresh allocation: `needle-role-skill-joint-retention-20260928-v3`, issue #4941, branch `research/needle-role-skill-joint-retention-v3-20260928`, path `research/system1/needle_role_skill_joint_retention_v3_20260928/`. Intake main: `519f2c1bdb219697c2f5e92ae6c27714265d60e`. Candidate lineage is #4911 / `research/needle-role-skill-joint-retention-v2-20260928`; predecessor allocation and STOP remain unchanged. This rung only checks launcher/output boundary and runs the zero-update suite. No optimizer step or formal seed is authorized.

### D
Construction boundary PASS only if tests show logs and receipt remain outside output, output starts empty, stale output/log paths and aliasing stop before subprocess, and the copied v2 source contract tests pass. No scientific PASS is inferred. Any unexpected failure is retained without rerun.

### C
One pinned local Docker invocation: cached image `needle-pilot05:local`, immutable image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, network none, read-only root/source, 1 CPU, 2 GiB, 64 PIDs. Logs use a separate writable mount; runner output uses a separate empty writable mount.

### U
Synthetic protocol-construction evidence only. No construction seed fit, online LoRA update, model/task quality, real role detection, GPU claim, or integrated Needle performance. Formal seeds 9944211/9944311/9944411 are reserved but unspent.
