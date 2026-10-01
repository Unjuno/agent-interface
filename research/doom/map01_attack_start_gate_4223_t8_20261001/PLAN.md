# Issue #4223 — T8 real-game startup gate

T8 is a fresh allocation after two preserved setup STOPs: T6 reached the
candidate but its output bind mount denied log creation; T7 stopped before a
candidate because a mechanical package-name rewrite requested nonexistent
`libxext7`. Neither predecessor is altered or rerun.

## H / T / D / C / U

**H.** On the exact pinned runtime image, changing only each dedicated
candidate/auditor output directory to mode 0777 and proving a container-side
write/readback under the same network-none, readonly-rootfs,
capability-dropped constraints lets the actual candidate preserve its logs and
advance to real DoomGame readiness and the first exact observation.

**T.** Allocation `MAP01-ATTACK-ONSET-STARTGATE-4223-T8-20261001-01` on this
additive path. Prefer the currently responsive local OrbStack daemon; target
linux/amd64 emulation. Download and verify offline runtime artifact 10398313098
(ZIP SHA-256
`522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`), every
2,592 source files and all 12 wheels; build the digest-pinned Python 3.13.5
image with the verified Debian package name `libxext6`. For each dedicated
output directory only: set mode 0777, record host UID/GID/mode, run an isolated
container write/readback probe under the frozen security constraints, verify
the probe from the host, and remove the probe file. Invoke exactly one
`session_map01_v13.py` candidate at seed 992600 / skill 1 / timeout 60 s via
private Xvfb/Openbox; require ready and the exact sequence-1 observation, hash
the PNG/RGB pixels, send only neutral `finish`, and retain exact stdout/stderr
and exit evidence. Invoke one independent raw-only auditor iff candidate exit
is 0. Retries/replacements: 0.

**D.** `PASS_START_GATE_ONLY` iff provenance/platform and both mount probes
pass, the actual game emits ready-before-exact-initial, image hashes match,
only one finish command is sent, no input-admission event appears, child exits
0, source hashes close against the manifest, and the independent auditor
reports zero errors. Otherwise preserve the exact STOP/FAIL and do not rerun.

**C.** Local OrbStack is available now; the prior local mode-0777 mount probe
on the cached linux/amd64 ViZDoom image allowed root, nobody, and host UID:GID
to write/read under `--cap-drop ALL`. That probe was construction evidence,
not the actual runtime candidate. OrbStack host is arm64 and will emulate
linux/amd64. T6's GitHub-hosted runner was a different filesystem/daemon
boundary; local success cannot erase or reproduce its STOP.

**U.** Technical startup/output preservation only. No attack, physical-edge,
TASK_EFFECT, onset-phase discrimination, recovery, map clear, model, or product
claim. PASS does not itself authorize the separate eight-session onset study.

## Execution accounting

- Frozen base main: `316c01a7eee60d776cb83ec779fb6745e9e7c2ca`.
- Formal candidate budget 1; retry budget 0; auditor budget 1 after candidate
  exit 0. Output-mount probes are separate explicitly-accounted construction
  probes and do not launch the game.
- The frozen source commit is recorded in `OBSTAC_EXECUTION.json`. Run the
  exact local command shown in `LOCAL_CI.md`; do not add a PR-triggered
  candidate job or rerun after opening a PR.
- Preserve result, raw files, hashes, independent audit and limits in
  `REPORT.md` and on Issue #4223 before pushing the evidence branch.
