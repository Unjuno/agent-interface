# Issue #4223 — T9 native x86_64 startup discriminator

T9 is a new environment-comparison allocation after T8's one local OrbStack
candidate exited `-11` before readiness under linux/amd64 emulation on a
linux/arm64 host. T6's hosted output-mount STOP and T7's package-build STOP
remain preserved; none is rerun.

## H / T / D / C / U

**H.** On a native x86_64 Docker host, the same pinned ViZDoom runtime and
T8's permission-repaired dedicated output mounts complete the real startup
gate and preserve first-observation evidence. If native x86_64 also fails
before readiness, OrbStack emulation alone is not sufficient to explain the
prior SIGSEGV.

**T.** Fresh allocation `MAP01-ATTACK-ONSET-STARTGATE-4223-T9-20261001-01`,
additive path `research/doom/map01_attack_start_gate_4223_t9_20261001/`.
GitHub Actions `ubuntu-24.04` is explicitly selected because it is native
x86_64 Docker and OrbStack's Linux VM is arm64. On PR-open, attempt 1 only:
verify immutable offline artifact 10398313098 and SHA-256
`522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`, all
2,592 sources and 12 wheels; build pinned Python 3.13.5 image with correct
Bookworm `libxext6`; record host architecture, Docker/server versions and
image ID. Make only the dedicated evidence output dirs mode 0777, run
container-side write/readback probes under network-none, readonly-rootfs,
cap-drop-all, no-new-privileges and resource bounds, and verify on host.
Invoke exactly one real `session_map01_v13.py` candidate, seed 992600 / skill1 /
timeout60, private Xvfb/Openbox, ready and exact initial observation, recompute
PNG/RGB hash, issue only neutral `finish`, preserve raw/stdout/stderr/exit.
Run one independent raw-only auditor only if candidate exits 0. Candidate
retry/replacement budget 0; workflow reruns excluded by `run_attempt == 1`.

**D.** `PASS_START_GATE_ONLY` iff host is native x86_64, provenance/image and
both write probes pass, real game produces ready before exact initial
observation, only `finish` is sent, no input admission is recorded, child exits
0, source hashes close against the verified manifest, and the independent
auditor reports zero errors. Otherwise retain the exact STOP/FAIL and do not
rerun T9.

**C.** GitHub-hosted Ubuntu/Docker is used only because local OrbStack reports
Linux/arm64 and T8's amd64-emulated child segfaulted. This environment is a
distinct host and not an OrbStack replication. The PR-open workflow itself is
the formal execution; after it finishes, report and verify its immutable
artifact before merge. Do not run another candidate locally or via workflow
rerun.

**U.** This discriminates scoped runtime startup across native versus emulated
x86_64 only. It does not test attack input, physical edges, TASK_EFFECT,
onset-phase discrimination, recovery efficacy, map clear, model quality,
latency, human tempo or product readiness. PASS does not authorize the separate
eight-session onset allocation.

## Execution accounting

- Frozen base main: `17d7d1a1ad4919fa77602cd0e0c5c0c4bc211563`.
- Exactly one candidate, no retries/replacements; auditor at most one after
  candidate exit 0. Preflight mount probes are separately recorded.
- The only formal trigger is PR-open on the private branch, attempt 1. The PR
  will not be merged until the uploaded run artifact is downloaded, digest
  checked, inspected, and this report plus Issue result are added.
