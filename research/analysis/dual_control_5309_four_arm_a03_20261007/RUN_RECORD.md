# A03 formal run record

- Allocation: `5309-FOURARM-A03-HOSTCPU-20261007`.
- Frozen main: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- Freeze: `FREEZE.json`; frozen candidate/auditor/truth/receipt-schema hashes are recorded there.
- Runtime: Python 3.14.5, host CPU, stdlib-only; no network API, GUI, model, OS input, or live authority. OrbStack was Running but `docker ps` failed on containerd blob `sha256:08e8b41ebd1476eff067939e0192d49e4014c21bab11a4d793429187e4242704` with `operation not supported`; no container was started and no image identity is claimed.
- Candidate formal command: `python3 candidate.py > candidate-raw.json 2> candidate.stderr.txt` — exactly one invocation; exit 0; stderr empty.
- Auditor formal command: `python3 auditor.py candidate-raw.json > audit.json 2> auditor.stderr.txt` — exactly one invocation; exit 0; stderr empty.
- Formal retries: zero. Candidate raw SHA-256: `dc94c4767999fe1a7ec78993bfbca6e1c16dd3f719e5dbf9fd04dfc0b464e4d7`. Audit SHA-256: `5951ce0e4ab58a20df5a02441385707e9b6ace71ac5670adb6c332ce1f242038`.
- Auditor disposition: `PASS_DUAL_PURPOSE_ACTION_SCOPED`, 112 rows, no audit errors; 136 pinned-schema execution receipts replayed. Primary fresh means: TASK_ONLY 3.0, EXPLICIT_SAFE_PROBE 4.0, DUAL_PURPOSE 2.0 synthetic cost units. Cost-reversal sensitivity: EXPLICIT_SAFE_PROBE 4, DUAL_PURPOSE 6, TASK_ONLY 6 total units.
- Local pre-formal checks: 17 construction tests passed; Python syntax compilation passed; exact receipt snapshot byte/hash comparison passed; workspace index Git-tree check reported 160 top-level research directories OK. The compact analysis-results index remains a sparse-checkout/full-CI gate.
- Do not run candidate or auditor again under this allocation. Post-run checks may inspect saved files, hashes, and CI results only.
