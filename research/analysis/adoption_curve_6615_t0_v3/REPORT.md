# Issue #6615 — adoption-inclusive verified-work curve (T0C)

Allocation `ADOPTION-INCLUSIVE-CURVE-6615-T0C-20261002-01`  
Status: `PASS_METHOD_SCOPED` (deterministic synthetic accounting-method validation only)  
Frozen base: `afea9a530cafd7af529df4c9e59f36b816bca24f`  
Execution: host-local CPython 3.14.5 on macOS; WSLc unavailable and shared OrbStack daemon did not respond to a read-only probe. No container-specific behavior was needed.  
Predecessors: T0 `../adoption_curve_6615_t0_v1/FORMAL_FAILURE.md`; T0B `../adoption_curve_6615_t0_v2/FORMAL_FAILURE.md`. Neither predecessor evidence set was modified.

## Protocol and execution

Nine frozen synthetic scenarios, two routes, 58 event rows. Construction tests: 6/6 passed. After freeze: exactly one candidate invocation (exit 0; 58 rows) and one separate auditor invocation (exit 0; 58/58 reconstructed; `errors: []`); no retries. Candidate stdout allocation was checked exactly against both fixture and FREEZE before audit interpretation. Five corruption controls rejected dropped setup failure, attempted-as-success, unsupported-as-success, dropped setup cost and free repair. Unsupported-host has no comparable prefix.

The first jointly verified quality-preserving break-even in the stipulated learning fixture is prefix 5: guarded cumulative wall cost 95s versus direct 100s. At prefix 4 the costs are guarded 95s versus direct 80s. The setup-dominates fixture has no break-even through K=5 (170s guarded versus 100s direct). Zero-delta ties at prefix 0. The ledger separately records one supported setup failure, one wrong/unverified attempt, one route-ineligible attempt, and zero unsupported-host successes. A guarded app-change repair contributes 30s wall/15s active time (the third guarded task event totals 38s wall/20s active including task execution).

## Interpretation and limits

`PASS_METHOD_SCOPED` supports only that the frozen event-ledger/accounting implementation distinguishes setup, repair, task costs, unsupported routes and verified effects under these stipulations, and reconstructs them independently. It does not measure actual first-use burden, operator effort, installs, credentials, host support, model cost, task mix, adoption, user preference, efficacy, or product economics. No real-host or telemetry collection was attempted. The crossing is an intentionally stipulated finite synthetic example, not a population estimate.

## Reproduction and hashes

From this directory, run `python3 -m unittest -v test_curve.py` for construction tests; the formal candidate and auditor each ran once against `fixture.json` and `raw.json`. All primary artifacts, raw stdout/stderr and audit are retained here.

SHA-256:

```
4949edd46665bc6e91f245acd8167391e03cb0882b4b70eb67a3e8cde626d465  candidate.py
7c806f6833697e8fd7b0dcba3ba502ac953fd5e23949d46d553b5b71e3f8a47f  auditor.py
c450de93ab5ebb8e99c1772b6455aac54aa00034a3635c3e918b9845c7d238d9  fixture.json
b46ca51af90d4ec3ee26e0afd697794b33a77abbac7f9c5b86d0274bcae83a61  test_curve.py
27f97d5fc9c62264764e72b1184da68b667fe4c6f40184a96c6bcd7ba4896d18  preregistration.md
8f4b045a730c161fb4aee5834b426b78d851011a4908f1e3b3bcb7d415900c86  FREEZE.json
49feb536ea5ff7d26e9536a3c0a5cee37f122a8f428d12b2f5083d798c86eb29  candidate.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  candidate.stderr
40afe8a6a7f039b39dcf4f3541a9db6749253e31e2b1009bb2bd62fe42e77815  raw.json
e6ef0790312ab7548000e1023e423d9275eef23fdad61bc13e79889a74874cb8  auditor.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  auditor.stderr
e6ef0790312ab7548000e1023e423d9275eef23fdad61bc13e79889a74874cb8  audit.json
```
