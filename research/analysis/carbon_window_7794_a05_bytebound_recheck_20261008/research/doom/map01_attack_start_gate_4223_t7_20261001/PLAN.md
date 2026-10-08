# Issue #4223 — T7 real-game startup gate

This is a fresh technical successor to T6's output-mount STOP. T6 remains
immutable. T7 is not an attack-onset comparison and does not modify or pool
allocations 01–04.

## H / T / D / C / U

**H.** On the current pinned Linux/amd64 ViZDoom image, making only the
candidate and auditor evidence output directories writable (mode 0777), while
retaining `--cap-drop ALL`, `no-new-privileges`, readonly source/rootfs,
network-none and resource bounds, permits a container-side write/readback and
the real startup candidate to preserve its artifacts. The candidate can then
initialize DoomGame through Xvfb/Openbox and emit its exact initial observation.

**T.** One fresh allocation, `MAP01-ATTACK-ONSET-STARTGATE-4223-T7-20261001-01`,
on additive path `research/doom/map01_attack_start_gate_4223_t7_20261001/`.
Prefer local OrbStack. Verify artifact 10398313098, its SHA-256, all 2,592
runtime source files and 12 wheels; build the pinned Python 3.13.5 Linux/amd64
image. For each dedicated output directory only: apply mode 0777, record host
UID/GID/mode, perform a container-side write/readback probe under the same
security constraints, verify its contents on the host, and remove the probe.
Then invoke exactly one `session_map01_v13.py` candidate at seed 992600 / skill
1 / timeout 60 s through private Xvfb/Openbox. Require ready plus exact
sequence-1 observation, recompute PNG/RGB hashes, issue only neutral `finish`,
and preserve stdout/stderr and exits. Invoke one independent raw-only auditor
only after candidate exit 0. Candidate/auditor retries and replacements: 0.

**D.** `PASS_START_GATE_ONLY` only if provenance/image/platform, both isolated
mount write/readback probes, actual DoomGame readiness, first exact observation,
finish-only, child exit 0, complete logs and independent raw audit all pass.
Otherwise retain exact STOP/FAIL; no rerun of this allocation.

**C.** The prior local two-arm OrbStack probe used cached image
`map01-attack-onset-formal:20260927`, image ID
`sha256:c88bce85f2b7f9fce294b8295440b3fa478990cda8b19b12de40dadbdc0e2c5c`.
On OrbStack, root with all capabilities dropped wrote successfully on a mode
0700 macOS temporary bind mount; the host-UID:GID arm did not see the mounted
path. On a mode-0777 disposable mount, root, nobody, and host-UID:GID all wrote
and read back. This is local mount-construction evidence, not the T6 hosted
failure reproduction. The fresh exact-runtime T7 experiment runs on OrbStack
Linux/amd64 emulation. Any transport fallback must be recorded, not relabeled.

**U.** Startup/output preservation only. No attack, physical-edge,
TASK_EFFECT, onset-phase discrimination, recovery, map clear, model, or product
claim. PASS does not itself authorize the separate eight-session onset study.

## Execution accounting

- Frozen base main: `b508e5aafc4781063b20b83f34e941094147d354`.
- Formal candidate budget 1; retry budget 0; raw-only auditor budget 1 after
  candidate exit 0.
- The hosted workflow is PR-open/attempt-1 only and checks main drift before
  formal candidate invocation. Local OrbStack execution, if it reaches the
  complete frozen gate, is the primary allocation result; the PR workflow is
  transport validation only and must not invoke a second candidate.
- Record exact command, source/image identities, raw outcome, independent
  audit, artifact hashes and scope limits in `REPORT.md` and on Issue #4223.
