# T8 execution report — STOP on native child crash

## Outcome

**STOP_CANDIDATE_CHILD_SIGSEGV_BEFORE_READY**. The new output-directory
permission gate worked: the constrained candidate container wrote and read
back its probe at mode `0o777`, and the candidate preserved its Xvfb/Openbox
logs and `RAW.json`. However, the one game child exited `-11` (SIGSEGV) after
launch and before emitting any JSON event. There was no `ready`, initial
observation, PNG, command, or task-effect evidence. Candidate container exit
was 1; the independent PASS-gate auditor was correctly skipped. This does not
establish whether the crash is ViZDoom or the OrbStack amd64-emulation path.

## Frozen run and raw evidence

- Allocation: `MAP01-ATTACK-ONSET-STARTGATE-4223-T8-20261001-01`
- Frozen source commit: `9858aca75f997893a3f0bcab5058b6725dcc41c9`
- Engine: OrbStack Docker Engine 29.4.0, Linux/arm64 host; container target
  linux/amd64 (emulated).
- Image ID: `sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe`.
- Runtime artifact 10398313098; ZIP SHA-256
  `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`.
- Offline closure: 2,592/2,592 source files and 12/12 wheels verified.
- Candidate mount probe: exit 0, container UID:GID `0:0`, mode `0o777`.
- Candidate invocation: 1; candidate container ID
  `e989c09c0380cc3975cb29ab25e5fc6e8c8ea9a290f051fc8c0c6ae36b69b474`;
  child PID 8 / return code -11; auditor invocations 0; retries 0.
- The retained `evidence/` directory contains OBSTAC execution receipt,
  artifact verification, runtime manifest, image build/inspect logs, mount
  probe log, candidate container log, and candidate RAW/Xvfb/Openbox/runtime
  files. The 20 runtime source hashes listed in RAW match the artifact
  manifest; all 2,592 source files and 12 wheel files passed the package
  verifier. The downloaded artifact ZIP matched its expected SHA-256.

## Interpretation and scope

This local OrbStack result confirms only that the dedicated mount permission
repair worked under its local container security settings and that the game
child crashed before readiness. Because the host is arm64 and the image is
amd64 emulated, the result cannot distinguish an emulator/native-library issue
from a general game-startup issue. No input or model was used. This is not an
attack-onset, physical-edge, TASK_EFFECT, recovery, map-clear, or product
result. T6's hosted-runner mount STOP and T7's package-name build STOP remain
separate immutable outcomes.

T8 is not rerun. A distinct native x86_64 Docker successor is needed to
separate the architecture/emulation boundary from the game startup itself.
