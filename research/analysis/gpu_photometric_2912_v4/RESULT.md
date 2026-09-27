# Formal result — Issue #4482

## Disposition

**`HOLD_NO_SAFE_BENEFIT`** for the preregistered photometric-augmentation claim. The corrected local GPU allocation completed intact, but augmentation did not strictly improve exact-coordinate grounding on any perturbed held-out case. No false coordinate was accepted. This is not a failure of execution or audit, and it is not evidence that augmentation is generally useless.

## Frozen design and execution

- Allocation: `gpu-photometric-2912-cnn-shape-4482-01`; exactly one formal runner invocation, no retry.
- Source intake: main `21dd6a26dbd9f5cb4a6e11b1060902799a76a733`.
- Frozen code commit: `a06e7013f614fe254f9b4cfca838b8077fae3aa9`.
- Freeze SHA-256: `083f5387cfa035568b3d56e467cab18a90d7ca73cfb25c981fe4e7fe80560233`.
- Local GPU: NVIDIA GeForce RTX 3080 Laptop GPU, 16 GiB; preflight 16,167 MiB free; C: free 323,134,832,640 bytes.
- Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1; deterministic algorithms on, TF32 off, `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
- Runtime: process began 2026-09-26 14:16:10.816 UTC and exited 0 at 14:16:16.994 UTC. Exactly 300 optimizer steps per arm (600 total); recorded training time 1.2445 s and 0.9812 s; peak allocated VRAM 97,987,072 bytes per arm.
- Source manifest and all six whole-image hashes matched. Training tasks were task-1, task-2, task-4 and task-5; held-out tasks were task-3 and task-6.

## Audited outcome

| Arm | Exact coordinates | Accepted wrong | Accepted | Yield | Perturbed exact |
|---|---:|---:|---:|---:|---:|
| No augmentation | 6/6 | 0 | 5 | 1 | 4/4 |
| Brightness augmentation | 6/6 | 0 | 6 | 0 | 4/4 |

Both arms were exact on all six held-out task/brightness rows. Augmentation was no worse in each of the four perturbed cases, but none strictly improved: `strict_case_gain=false`. All 12 candidates passed the strict schema/bounds validator; both arms had zero accepted false coordinates. The frozen decision therefore remains HOLD, not PASS.

Descriptive only: the no-augmentation arm yielded on task-3 at 0.85x brightness (confidence 0.5457); the augmented arm accepted the same exact coordinates there (confidence 0.9994). The other five cases were accepted by both arms. This six-row, two-source observation is not a calibrated confidence, safety, or utility result and does not override the preregistered exact-coordinate gate.

Independent raw auditor: exit 0, status `HOLD_NO_SAFE_BENEFIT`, six source images verified, errors none. The separate preformal suite remains 9 tests passed and 18/18 mutation subtests rejected.

## Evidence

Exact process files are retained under `results/formal01/` with raw bytes preserved by this directory's `.gitattributes`. `SHA256SUMS.txt` lists their SHA-256 digests and the preregistered source pins. `results.json` SHA-256: `6541877a19ee8ffdd91899e7626515931daf83dae89e316d0754d1ec3d678690`; independent `AUDIT.json` SHA-256: `89937b208ac30dac7169712d015abfe6ff9a908559f3c2796211a7e180a3eb30`.

## Limits and handoff

Only two held-out source images (one per layout) and their brightness variants were evaluated. The variants are repeated conditions, not independent source samples. No unseen-layout generalization, calibration, live GUI, action authority, runtime integration, latency/token benefit, or product claim is supported. The routing-yield difference may motivate a separate, newly preregistered study only if additional untouched source images can be identified; do not rerun or widen this consumed allocation. No model is promoted.
