# Formal run record

- Source freeze commit: `2d2785f1619c98b103b7f1a4f5abb9f32da49476` (parent main `cdfebdb125e0566d2cbe741c4925b94eb17b439b`).
- Source blob SHA values were re-read from GitHub at the freeze commit and matched local frozen bytes.
- Formal command, once: `python candidate.py` (stdout retained byte-for-byte as `candidate_output.json`).
- Independent audit command, once: `python auditor.py` (stdout retained byte-for-byte as `audit.json`).
- Exit status: candidate `0`; independent auditor `0`.
- Result: 10 cases, independent truth-table error count 0; all five frozen controls true.
- Runtime: host Windows CPU/Python 3.12. Docker daemon was stopped; no lease was assigned for the shared container pool. No network/model/GUI/input calls occurred during the experiment.
- Formal reruns: none. The earlier construction attempts were separate pre-freeze checks and are not part of these formal outputs.

Exact auditor stdout:

```json
{"auditor":"independent-truth-table-v1","controls":{"exact_trace_covers_policy_decision":true,"invalid_deletion_untestable":true,"redundant_proofs_accepted":true,"stale_policy_detected":true,"uncited_decisive_detected":true},"error_count":0,"errors":[],"rows":[{"candidate_flag":false,"expected_defect":false,"id":"necessary-citation","issues":[],"truth":"ALLOW"},{"candidate_flag":false,"expected_defect":false,"id":"alternative-proof-fresh","issues":[],"truth":"DENY"},{"candidate_flag":false,"expected_defect":false,"id":"alternative-proof-lease","issues":[],"truth":"DENY"},{"candidate_flag":false,"expected_defect":false,"id":"redundant-independent-proofs","issues":[],"truth":"ALLOW"},{"candidate_flag":false,"expected_defect":false,"id":"context-only-citation","issues":[],"truth":"ALLOW"},{"candidate_flag":true,"expected_defect":true,"id":"uncited-decisive-receipt","issues":[],"truth":"DENY"},{"candidate_flag":true,"expected_defect":true,"id":"stale-epoch-citation","issues":[],"truth":"ALLOW"},{"candidate_flag":false,"expected_defect":false,"id":"valid-contradictory-replacement","issues":[],"truth":"DENY"},{"candidate_flag":true,"expected_defect":true,"id":"invalid-mandatory-deletion","issues":[],"truth":"UNTESTABLE"},{"candidate_flag":true,"expected_defect":true,"id":"policy-swap-stale-explanation","issues":[],"truth":"DENY"}]}
```
