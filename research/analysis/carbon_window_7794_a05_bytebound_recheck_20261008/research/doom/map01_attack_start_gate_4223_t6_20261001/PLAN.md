# Issue #4223 — T6 real-game startup gate

This is a fresh technical successor to the consumed allocation-04 STOP. It is
not an attack-onset comparison and does not modify or pool allocations 01–04.

## H / T / D / C / U

**H.** Using the exact offline runtime source/wheel artifact from source base
`9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`, a newly built pinned Python
3.13.5/Linux-amd64 image can initialize the real ViZDoom `DoomGame` through
private Xvfb/Openbox, emit `ready` and its exact initial RGB observation, then
accept only `finish` and exit 0 while preserving child exit/stdout/stderr.

**T.** One candidate invocation on a GitHub-hosted Ubuntu 24.04 Linux/amd64
Docker runner is allowed because the local OrbStack daemon remains unavailable
and this is not a shared local-engine slot. Download artifact 10398313098 and
verify ZIP SHA-256
`522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`; verify
all 2,592 source files and 12 offline wheel files against its manifest; build
from the digest-pinned `python:3.13.5-slim-bookworm` base; record actual image
ID, platform, apt package versions, and OBSTAC receipt. Candidate and auditor
containers use `--network none`, read-only root/source, bounded resources, and
separate writable evidence directories. The candidate starts
`session_map01_v13.py` at seed 992600 / timeout 60 s / skill 1, waits for the
first exact image, then sends one neutral `finish` command (no gameplay key or
model call). One separate raw-only auditor runs only if the candidate exits 0.
No retries or replacements; Actions reruns are excluded by the workflow gate.

**D.** `PASS_START_GATE_ONLY` requires exact artifact closure, image/platform
receipt, Xvfb/Openbox startup, child `ready` preceding sequence-1 `initial`
observation, nonempty PNG whose recomputed RGB SHA matches the event, exactly
one `finish` command, zero input-admission events, one post-control score,
child exit 0, complete stdout/stderr, runtime source hashes matching the
artifact manifest, and independent audit with zero errors. Any failed gate is
retained as STOP/FAIL; no retry.

**C.** This is a GitHub-hosted Linux/amd64 Docker execution, not OrbStack and
not byte-identical to the historical custom image. The Python base is pinned;
APT package versions and final image ID are captured at build time. Build-time
network is used only for OS packages; candidate/auditor runtime networking is
disabled. This does not infer why allocation 04 stopped.

**U.** Startup/readiness only. No attack key, physical-edge measurement,
TASK_EFFECT, onset-phase result, recovery result, MAP01 clear, or user-tempo
claim. A PASS does not itself authorize the eight-session scientific allocation;
that requires a separate fresh freeze and ownership check.

## Execution accounting

- Allocation: `MAP01-ATTACK-ONSET-STARTGATE-4223-T6-20261001-01`.
- Source base: `33c19225f117d6d927a98e791e620de37479a927`.
- The PR-open job rereads current `main`; it permits only descendant, disjoint
  updates and stops before candidate if README/current-goal/roadmap or the
  related #4223/#4193 evidence paths changed after this freeze.
- The PR-open job rereads current `main`; it permits only descendant, disjoint
  updates and stops before candidate if README/current-goal/roadmap or the
  related #4223/#4193 evidence paths changed after this freeze.
- Formal candidate budget: exactly 1; retry budget: 0.
- Independent auditor budget: 1, only after candidate exit 0.
- Artifact ID/SHA and commands are recorded in `OBSTAC_EXECUTION.json` and raw
  evidence. `REPORT.md` will be completed from the immutable uploaded artifact.
