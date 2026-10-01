# Issue #4223 — T10 native Docker startup gate

T10 is a fresh, one-shot successor to T9. T9 reached the real game child on a
native x86_64 Docker host but stopped before `ready`: the verified source
called `wmctrl -l`, while the pinned image omitted `wmctrl`. T8's OrbStack
linux/amd64-emulated child had separately exited `-11`; T10 does not repeat or
rewrite either predecessor. T6 and T7 remain distinct preserved STOPs.

## H / T / D / C / U

**H.** Installing and build-preflighting the exact `wmctrl` executable will
remove T9's first identified image dependency gap; on native x86_64, the
candidate will then reach its frozen startup/initial-observation gate, unless
another independent startup dependency or runtime failure intervenes.

**T.** Fresh allocation `MAP01-ATTACK-ONSET-STARTGATE-4223-T10-20261001-01`,
additive evidence path
`research/doom/map01_attack_start_gate_4223_t10_20261001/`. Before the single
candidate invocation, verify immutable runtime artifact 10398313098 and SHA-256
`522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`, all
2,592 source files and 12 wheels, native runner architecture and Docker
versions, pinned image identity, a build-time `command -v wmctrl` check, and a
constrained container-time `command -v wmctrl && wmctrl --version` check before
the game candidate is armed.
Use only dedicated writable output mounts for construction probes. Under
network-none, read-only rootfs, cap-drop-all, no-new-privileges and resource
bounds, invoke `session_map01_v13.py` exactly once (seed 992600, skill 1,
timeout 60), with private Xvfb/Openbox. Require `ready`, exact initial
observation and matching PNG/RGB digest; send only neutral `finish`; preserve
raw receipt, stdout/stderr, exit status, mount probes and image/build logs.
Run one independent raw-only auditor only after candidate exit 0. Candidate
retry/replacement budget is zero.

**D.** `PASS_START_GATE_ONLY` requires native x86_64, verified runtime and
image provenance, both required output-mount probes, `wmctrl` build preflight,
`ready` followed by exact initial observation, matching pixel digest, only
`finish` control, candidate exit 0, closed source hashes, and independent
auditor exit 0. Any failed condition is recorded with its exact STOP/FAIL
reason; it does not authorize a retry.

**C.** Local Docker/OrbStack is available but its Linux VM is arm64; T8's
linux/amd64-emulated game child segfaulted before readiness. T9 therefore
allocated a native x86_64 GitHub-hosted runner, which exposed the missing
`wmctrl` dependency after successfully starting Xvfb/Openbox. T10 keeps that
native runner as the controlled environment to test the dependency repair.
This is not a local experiment. The PR-open workflow is the one formal
execution; no rerun or second candidate is allowed. T10's evidence and result
must be locally validated and committed before PR merge.

**U.** The outcome is limited to this pinned image/runtime's startup and first
observation. It does not establish attack-input behavior, physical edges,
TASK_EFFECT, onset-phase discrimination, recovery efficacy, map clear, model
quality, latency, human tempo or product readiness. Even a pass cannot replace
the separate preregistered onset allocation.

## Execution accounting

- Frozen base main: `b3d3ed8315d016967f361a36b2d3d022adad66f0`.
- Formal candidate invocations: exactly one; candidate retries/replacements: 0.
- Independent auditor: at most one, gated on candidate exit 0.
- Only formal trigger: PR opened, workflow attempt 1. Evidence inspection and
  local CI must pass before merging the evidence/report PR.
