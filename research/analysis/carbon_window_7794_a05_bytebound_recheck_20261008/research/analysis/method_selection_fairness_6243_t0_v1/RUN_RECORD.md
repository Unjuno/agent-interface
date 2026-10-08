# Run record

- Allocation: `method-selection-6243-t0-v1-20261002-01`
- Frozen base: `fe37b6913f75706fc6bd536ae3afd6ed6a72b674`
- Candidate: `python3 candidate.py`, CPython 3.14.5, exit 0, one formal invocation.
- Auditor: `python3 auditor.py`, CPython 3.14.5, exit 0, one formal invocation; `METHOD_PASS_SCOPED`, 3 scenarios, 11 attempt-segment rows, `errors=[]`.
- Formal retries: 0. Construction retries/corrections are separately described in `FAILURE_CONSTRUCTION_01.txt` and README; no formal result was overwritten.
- Image/container: none. The shared-container gate in #5085 prevented another OrbStack/Docker launch while `unjuno-native-ci-6092` was active and no explicit slot release was present. The existing container was not inspected or modified.
- `obstac`: unavailable in this environment's CLI/tool inventory.
- Scope: deterministic synthetic accounting only. No network, GUI, model/provider, participant, account, physical input, or side effect.
- Outputs: `candidate.json` is the formal candidate record; `audit.json` is the independent raw-only audit record.
- Checks: pre-freeze Python compilation, JSON parsing, 11 construction assertions, and three mutation controls passed. Repository-wide CI was not run; this workspace is not a full repository checkout and the shared Docker slot is unavailable.
