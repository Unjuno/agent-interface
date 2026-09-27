# Issue #4682 result — STOP after independent-auditor path mismatch

**Allocation:** `issue4665-runtime-provenance-fixture-v2-20260927-01`  
**Intake main:** `fb7bb7c82baf2be614e6e1d14fd0245c48c81b87`  
**Final disposition:** `STOP_INDEPENDENT_AUDIT_PATH_MOUNT_MISMATCH`

The frozen package's construction tests passed 7/7 in local Docker. The single formal Docker allocation exited 0 and emitted `PASS_RUNTIME_BOUND_AUDIT_SCOPED`. Its host receipt matched Engine 29.8.0, daemon `linux/x86_64`, image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, image `linux/amd64`; in-container CPython was 3.12.14. Five preregistered one-field runtime mismatches (engine, daemon platform, image ID, image platform, Python) all produced `STOP_PROVENANCE_OR_ENVIRONMENT` with `semantic_audit_invoked=false`. The exact baseline ledger passed and the dropped-role, changed-digest, and wrong-path controls were rejected.

The separate raw-only audit container then exited 1 before producing an independent audit artifact. `verify_audit.py` expected `/evidence/formal01/AUDIT.json`, but the formal output mount was the host directory `results/formal01` mounted at `/out`, while the runner writes `/out/formal01/AUDIT.json`. The actual preserved location was therefore `results/formal01/formal01/AUDIT.json`. The observed `FileNotFoundError` is retained in `results/independent-attempt.stdout.txt`; no independent PASS is claimed.

Per the frozen no-retry/no-post-result-tuning rule, the verifier path or mount layout was not changed and the audit was not rerun. Therefore the scoped formal runner PASS remains raw evidence, but the successor allocation as a whole is STOP, not PASS. This does not alter #4665/#4675 or their evidence.

## Local Docker execution

All invocations used the cached exact image ID above, `--pull=never --network none --cpus=1 --memory=512m --pids-limit=32 --read-only`, with the package mounted read-only. The construction suite was:

```text
docker run --rm --pull=never --network none --cpus=1 --memory=512m --pids-limit=32 --read-only <package-ro-mount> <image-id> python -B -m unittest discover -s /study -p test_*.py -v
```

Formal execution mounted study and inputs read-only, runtime receipt read-only, and a fresh output directory writable:

```text
docker run --rm --pull=never --network none --cpus=1 --memory=512m --pids-limit=32 --read-only <study-ro> <inputs-ro> <runtime-receipt-ro> <fresh-output-rw> <image-id> python -B /study/run_audit.py
```

The one independent-audit attempt mounted the evidence root at `/evidence`; the path mismatch above is the retained STOP reason. No GitHub workflow/Actions execution, provider/model, GUI/input, predecessor runner/auditor, or predecessor formal allocation was invoked.

## Evidence hashes

- `FREEZE.json`: `49300ae2b106f4c786d9c207af5307a0f66e1ad742db8f06c3d1eb9472bf7815`
- `results/runtime/receipt.json`: `7082eb55cf564fe689d2b3b2365160d89b77e9a3e9e01bb91c980f1ed5866e96`
- `results/formal01/AUDIT.json`: `35c0a46b289afe764b3c6c779117c17c35490639530c6e0affba00e2ed0d93fb`
- `results/formal01/stdout.txt`: `1aa645057b534042ec178b9cb67dff9a42b1bd11ce1cd29a9e0bd80f2f52ffbc`
- `results/independent-attempt.stdout.txt`: `28c76ac1e1c4ba89f1bcb0928916ba1c6baf5eeff956c207f54a5126a34dacf9`

The study package preserves all ten input-role bytes and the predecessor manifest byte-for-byte. This STOP does not recover #4649's unpublished formal ZIP or support any runtime/product claim.
