# Executed run record — W2 Draft 2020-12 meta-validation

Source pin: latest main at pre-PR revalidation `04564ff4d1df59f01a91de7338c44adab9ae74ab`. Schema/case blob IDs were re-fetched at that SHA and still match `ebc424d2df631aa74c6d9aee4699c595a27ed589` and `0a49a00567c25766495cd332be50f6c2946781f7`.

Container: Docker Desktop `python:3.12-slim` image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, CPython 3.12.14. jsonschema 4.25.1 dependencies were resolved and downloaded on the host before the run, SHA-pinned in `PLAN.md`, then installed in-container only from a read-only wheelhouse with pip `--no-index`. All container invocations used network none, pull-never, read-only root, read-only source and wheelhouse, caps dropped, no-new-privileges, 0.25 CPU, 256 MiB, 32 PIDs, and explicit executable `/tmp` tmpfs for loading the pinned native extension.

## Preflight only

Command (PowerShell resolves the three bind-source directories):

```text
docker run --rm --network none --pull=never --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --cpus 0.25 --memory 256m --mount type=bind,source=<study>,target=/study,readonly --mount type=bind,source=<wheelhouse>,target=/wheelhouse,readonly --mount type=bind,source=<preflight-v3>,target=/out --tmpfs /tmp:rw,exec,nosuid,size=96m -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python -B /study/docker_run_audit.py --preflight --script meta_audit.py --out /out
```

Exit 0. `preflight.stdout` reports `jsonschema 4.25.1` and the loaded `rpds` module. No schema validation function was invoked.

## Candidate audit — allocation 03, one invocation

```text
docker run --rm --network none --pull=never --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --cpus 0.25 --memory 256m --mount type=bind,source=<study>,target=/study,readonly --mount type=bind,source=<wheelhouse>,target=/wheelhouse,readonly --mount type=bind,source=<results-v3>,target=/out --tmpfs /tmp:rw,exec,nosuid,size=96m -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python -B /study/docker_run_audit.py --script meta_audit.py --out /out
```

Docker/launcher exit 0; audit subprocess exit 0. `audit.json` states 8 valid instances, seven rejected schema mutations, seven rejected instance mutations, and exact source SHA-256s. The raw stderr is retained; it contains `SystemExit: 0` (14 bytes), caused by the candidate script's top-level exception logger catching its normal zero `SystemExit`. Do not hide that output; it is not the subprocess status and did not change result JSON.

## Separate independent recheck

```text
docker run --rm --network none --pull=never --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --cpus 0.25 --memory 256m --mount type=bind,source=<study>,target=/study,readonly --mount type=bind,source=<study>,target=/source,readonly --mount type=bind,source=<results-v3>,target=/evidence,readonly --mount type=bind,source=<wheelhouse>,target=/wheelhouse,readonly --mount type=bind,source=<independent-v3>,target=/audit-out --tmpfs /tmp:rw,exec,nosuid,size=96m -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python -B /study/docker_run_audit.py --script independent_audit.py --out /audit-out
```

Separate container exit 0, audit subprocess exit 0, stderr empty. Auditor source is independent of `meta_audit.py` and does not import it. It independently checks exact schema/cases SHA-256s, candidate-result SHA-256, `check_schema`, and all eight schema instances. It reports the candidate's 7+7 mutation counts; direct mutation execution is retained in candidate `audit.json`.

See `HASHES.txt` for exact local artifact SHA-256s and the two preserved pre-audit STOPs.
