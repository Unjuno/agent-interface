# Integrated focus recovery adapter v1
Task: INTEGRATED-FOCUS-RECOVERY-ADAPTER-20260917-001
Issue: #858
BASE: 7f8376c8e74a581bd884416b5313ce4cda756b68
Pinned full client Git blob: ace0366f2c5252c9dab3927c664cb58234b5ff03

H: current generic yield loses typed focus rejection; post-terminal no-authority adapter can preserve it with fresh B context without retrying input.
T: exact execute_handles control-flow transcription, deterministic fake transport, 3 reps x 2 policies, one formal invocation, reruns 0.
D: baseline generic 3/3; candidate typed fresh recovery 3/3; no authority, no post-rejection task submissions; negative controls fail closed.
C/U: contract integration only; no live GUI/model/token claim.
