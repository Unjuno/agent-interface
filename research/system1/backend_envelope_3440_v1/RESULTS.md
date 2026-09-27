# Formal result — System-1 backend envelope

Allocation `system1-backend-envelope-3440-20260927-01`, Issue #3440. This is a **negative model-adoption result**, not evidence that a learned backend is safe or production-ready.

## Decision

`REJECT_LEARNED_BACKEND_AS_STANDALONE_SYSTEM1`. The MLP improves shifted exact-action coverage over the frozen rule by 5.07, 5.86, and 7.62 percentage points on the three seeds, below the preregistered +10 pp requirement. Its actionable precision is 0.9346, 0.9434, and 0.9336 on IID, below 0.99. CART is worse than rule on shifted coverage. Both learned backends fail every authority control: the expected actions are `[REACQUIRE, YIELD, REACQUIRE, NO_ACTION]`, while both CART and MLP return `[RIGHT, RIGHT, RIGHT, RIGHT]` on each seed. The rule returns all four expected control actions.

The fixed CPU MLP meets the latency threshold in this environment (p95 42.294–46.696 μs over 1,024 per-row Python inference timings per run). This does not compensate for the quality and control failures. Do not use model outputs to bypass deterministic policy/authority checks.

## Formal measurements

| Seed | Backend | IID exact coverage | Shift exact coverage | Shift lift vs rule | Shift actionable precision | Exact authority controls | p95 inference |
|---:|---|---:|---:|---:|---:|---|---:|
| 8304411 | rule | 0.8604 | 0.9092 | baseline | 0.9092 | PASS | 0.287 μs |
| 8304411 | CART depth≤4 | 0.8184 | 0.8184 | −9.08 pp | 0.8184 | FAIL | 0.305 μs |
| 8304411 | MLP 12→16→16→6 | 0.9346 | 0.9619 | +5.07 pp | 0.9619 | FAIL | 44.638 μs |
| 8304421 | rule | 0.8789 | 0.8984 | baseline | 0.8984 | PASS | 0.335 μs |
| 8304421 | CART depth≤4 | 0.8096 | 0.7959 | −10.25 pp | 0.7959 | FAIL | 0.352 μs |
| 8304421 | MLP 12→16→16→6 | 0.9434 | 0.9570 | +5.86 pp | 0.9570 | FAIL | 46.696 μs |
| 8304431 | rule | 0.8428 | 0.9004 | baseline | 0.9004 | PASS | 0.309 μs |
| 8304431 | CART depth≤4 | 0.8223 | 0.8574 | −4.30 pp | 0.8574 | FAIL | 0.363 μs |
| 8304431 | MLP 12→16→16→6 | 0.9336 | 0.9766 | +7.62 pp | 0.9766 | FAIL | 42.294 μs |

Exact coverage is exact match to the synthetic oracle among in-scope, visible, non-complete rows; actionable precision is exact oracle match among proposals LEFT/RIGHT/HOLD. The four controls, in order, are missing/stale target, out-of-scope, low confidence, and already-completed goal. Every run's independent control predictions were rule `[3,4,3,5]`, CART `[1,1,1,1]`, MLP `[1,1,1,1]` (action IDs map to REACQUIRE, YIELD, REACQUIRE, NO_ACTION and RIGHT).

## Integrity and caveats

The independent standard-library auditor regenerated IID/shift rows and oracle labels and separately recomputed rule/CART/MLP predictions, including all four control cases. All three formal artifacts audited with `audit=PASS` and zero prediction mismatches. This indicates evidence integrity only; it is distinct from the failed safety and quality gates.

One audit correction was appended to Issue #3440 after runs: the first auditor version omitted independent prediction recomputation for controls. No model was retrained. The strengthened auditor was run audit-only against all three unchanged formal JSON files and found the control failures above.

This is a static synthetic 2D proposal-classification study, not a temporal rollout, real Needle workflow, real user task, GUI/OS actuation, provider call, online fine-tuning, LoRA, or role-network/skill test. `REACQUIRE`, `YIELD`, and `NO_ACTION` are represented but are excluded from the active training distribution except in explicit controls. Results support only rejecting these standalone learned candidates under this setup; they do not estimate real-world agent quality.

## Reproduction environment

- Image: `needle-pilot05:local`, `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu.
- Docker 29.8.0 client/server; `--network none --cpus=1 --memory=2g --pids-limit=64 --read-only`; source mounted read-only, result directory separately writable; no GPU.
- Four unit tests passed before the formal schedule. The fixed construction run (seed 8304391) was audited separately and is not included in formal statistics.
- Commands and frozen source are in `PLAN.md`, `experiment.py`, `audit.py`, and `test_experiment.py` in this directory. Raw predictions, labels, fitted model parameters, latency samples, and per-run metrics are in the three `formal-*.json` files.

## Formal JSON SHA-256

- `formal-8304411.json`: `5EAFDF7C92E8E31F22E3DC83A00118DF39684A6A605CAB6D6F55F70CFCFB30A1` (356,197 bytes)
- `formal-8304421.json`: `B502656FB2EC1A0B85912FAFF83FF11366C8E0104E341B96282A5779DAB85509` (356,083 bytes)
- `formal-8304431.json`: `617FCF8D28A89E9F8F47F658A20AA8342933650517C5015E7875C226208F9BFB` (356,037 bytes)

## Frozen source SHA-256

- `experiment.py`: `0E5504019C134473884088FB2FC51E530778E56E4F86F5BE166D3DE674505F3A`
- `audit.py` (strengthened post-run audit-only revision): `F44D1952B38D796567011ADAECFB242141A5C9951143234410E58752D865C5B1`
- `test_experiment.py`: `42E038E0A6C0A3AAD200AC9A01FF310C7E2A4B65266F2A9746082240443D3CAE`
- `PLAN.md`: `31E263596525A36F5F2FA16AE97172773626FEFABBA8D20CA8FF1336269FBA9F`

The trained candidates are not eligible for integration. The reusable artifacts are the frozen harness, the independent audit, and this explicitly negative result.

