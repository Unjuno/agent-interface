# A05 saved caller/compiled result audit

This package independently checks the merged PR #7384 task-1 result without replaying input. It pins the 360-member evidence manifest, confirms each member hash, replays the append-checkpoint journal verifier, binds receipt observations to saved screenshot bytes and image/predicate digests, reconciles compiled transitions to durable released terminals and later effect evidence, and matches the exact task token against append-only submission history.

The accepted disposition is deliberately scoped: `PASS_SCOPED_TASK1_EVIDENCE_INCOMPLETE_SIX_TASK`. The saved six-task oracle must report one exact task-1 record and tasks 2–6 missing. The audit rejects promotion to full-six success, ledger fabrication, transition/release mismatch, and submission-history mismatch. It does not certify raw-evidence provenance beyond the committed hashes, grounding cost, cross-task warm reuse, a model-efficiency benefit, or a full comparison.

Reproduce from the repository root:

```sh
python3 -B research/live_control/audit_chromium_client_single_task_v1.py
python3 -B -m unittest -v research/live_control/test_chromium_client_single_task_audit_v1.py
```
