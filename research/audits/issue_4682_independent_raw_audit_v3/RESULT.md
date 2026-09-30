# Issue #4687 result — PASS_INDEPENDENT_AUDIT_V3

**Allocation:** `issue4682-independent-raw-audit-v3-20260927-01`  
**Intake main:** `4011b8c8d83ecced9490b2e2f6ad60a2d62761e7`  
**Formal reruns:** 0  
**Independent verifier Docker invocations:** 1

Local Docker construction tests passed 3/3. The one fresh raw-only verifier container exited 0 with `PASS_INDEPENDENT_AUDIT_V3`, `errors=[]`. It reconciled the copied #4682 formal audit SHA-256 `35c0a46b289afe764b3c6c779117c17c35490639530c6e0affba00e2ed0d93fb`, observed receipt SHA-256 `7082eb55cf564fe689d2b3b2365160d89b77e9a3e9e01bb91c980f1ed5866e96`, v2 freeze SHA-256 `49300ae2b106f4c786d9c207af5307a0f66e1ad742db8f06c3d1eb9472bf7815`, all ten v2 input roles, all six v2 source files, the exact host runtime, baseline ledger PASS, three ledger-mutation rejects, and five pre-semantic runtime mismatch STOP controls.

The path contract was frozen as `results/formal01/AUDIT.json` mounted read-only at `/evidence/formal01/AUDIT.json`, with verifier output separately mounted at `/out`. This confirms the prior STOP was a mount-layout invocation defect. It does not retroactively change #4682's final allocation decision or rerun its formal audit; #4682 remains recorded as STOP pending its own frozen decision gate.

## Local Docker commands

Construction-only suite:

```text
docker run --rm --pull=never --network none --cpus=1 --memory=512m --pids-limit=32 --read-only <v3-study-ro> <image-id> python -B -m unittest discover -s /v3 -p test_*.py -v
```

One independent raw audit:

```text
docker run --rm --pull=never --network none --cpus=1 --memory=512m --pids-limit=32 --read-only <v2-study-ro> <v2-inputs-ro> <v3-study-ro> <formal01-directory-ro-at-/evidence/formal01> <runtime-receipt-ro> <fresh-output-rw> <image-id> python -B /v3/verify_successor.py
```

Exact image ID: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (Linux/amd64). Host receipt values: Docker Engine 29.8.0, daemon `linux/x86_64`, image platform `linux/amd64`; v2 container Python 3.12.14. All containers used network none and pull never. No GitHub Actions/workflow or predecessor formal runner was invoked.

## Evidence hashes

- v3 `FREEZE.json`: `0f8df3d25c35ed9e03a153940ffdca35c5940485bebd7484d247c3d68a449ca4`
- `results/INDEPENDENT_AUDIT.json`: `755360947089b030dd53628f22b67b2cbb08f4b17869f20cd19e1657466c9d53`
- `results/stdout.txt`: `4f3da4dd1760fe9781e807227c1a383c2c7ab1d376d3ff3176fb0fe1e0f1f94e`

Scope remains one retained synthetic audit/receipt consistency verification only. It does not recover #4649's unpublished ZIP, prove arbitrary auditor completeness, or establish runtime/product behavior.
