# Compiled typed decision kernel v1
Task: LOCAL-SYSTEM1-COMPILED-DECISION-KERNEL-20260917-001
Issue: #876
BASE: 275480a47f8f06e119b3eb66709b96dbf735bd4b

H: a fused NumPy typed-decision kernel remains under 60 ms warm single-state p95 at 16,777,216 float32 installed parameters while preserving fixed typed vocabularies and explicit YIELD.
T: parameter scale only: 262144 / 1048576 / 4194304 / 16777216. Fixed 32-float input, 455 logits across 33 typed heads, single-thread BLAS env, 16 warmups +128 measured queries/tier. One formal supervisor invocation, fresh child process per tier, fixed counterbalanced order [1M,16M,262K,4M], reruns0.
D: PASS iff all integrity/typed/YIELD/determinism gates pass and 16M p95<60ms. Also classify <10ms high-cadence and <1ms submillisecond. >=60ms => REJECT_COMPILED_KERNEL_60MS_SHAPE.
C: random weights measure runtime shape only; state extraction/calibration/usefulness may dominate real tasks.
U: one CPU/NumPy/BLAS/thread setup; no intelligence/model-quality/end-to-end claim.
