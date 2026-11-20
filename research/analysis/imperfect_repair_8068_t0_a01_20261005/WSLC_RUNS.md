# WSLc attempt record

Runtime: `wslc 3.0.1.0`; image `python:3.12-slim`, local image ID
`9e87977b8678`; `--pull never --network none --cpus 1 --memory 512M`.
Mounted candidate package read-only at `/src`. WSLc warned:

```text
wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.
```

Requested memory is not evidence of enforced memory isolation.

## Construction suite (one invocation)

```powershell
wslc run --rm --pull never --network none --cpus 1 --memory 512M --mount "type=bind,source=$srcPath,target=/src,readonly" -w /src python:3.12-slim python -c "import sys,unittest; sys.path.insert(0,'.'); s=unittest.defaultTestLoader.discover('.',pattern='test_*.py'); r=unittest.TextTestRunner(verbosity=2).run(s); raise SystemExit(not r.wasSuccessful())"
```

Outcome: 4/4 PASS.

## Candidate (one invocation; no retry)

```powershell
wslc run --rm --pull never --network none --cpus 1 --memory 512M --mount "type=bind,source=$srcPath,target=/src,readonly" --mount "type=bind,source=$outPath,target=/out" -w /src python:3.12-slim python -c "import run_candidate"
```

Outcome: STOP, exit failure before output. `run_candidate.py` writes to
`Path(__file__).with_name("candidate_raw.json")`, which resolves to read-only
`/src/candidate_raw.json`; it did not honor the intended writable `/out`
mount. This is an output-contract/setup defect. The candidate was not invoked
again.

## Auditor (one invocation over pre-existing host raw)

```powershell
wslc run --rm --pull never --network none --cpus 1 --memory 512M --mount "type=bind,source=$srcPath,target=/src,readonly" python:3.12-slim python -c "import sys; sys.path.insert(0,'/src'); import audit_raw"
```

Output:

```json
{"audited_rows": 12, "errors": [], "expected_rows": 12}
```

This independent audit result does not constitute a WSLc candidate pass.
