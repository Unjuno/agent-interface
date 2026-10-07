# A03 — native suite under WSLc

Allocation: `3352-native-suite-wslc-a03-20261004`  
Successor issue: #7357; next environment-closure successor: #7361  
Frozen source: `25700c9f68e9937fc1057a5da91d14c3971bb2b6`  
Workflow blob: `94213e369cdf28e05778bd0a38b26f1a18f8f14b`; Dockerfile blob: `f1464e51c2cc4e493c439f93fc049ccfe6221590`; runner blob: `d70fa82b1b29c4a384a95348697431ec3d28d2a0`.

## Protocol and preflight

Separate additive A03 path; A02 artifacts remain unchanged. The preflight audited 2,144 manifest entries / 10,634,390 bytes against Git blob SHA-1, found zero mismatches, confirmed the Dockerfile COPY input and all 54 declared modules using both configured PYTHONPATH roots. WSLc had zero active containers; output path was fresh.

One WSLc build succeeded with pinned `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. Image: `sha256:bf8083df20320e18478fb0ded90d90a73999b58aab1639220eb155c660576df6`.

One candidate used the image ENTRYPOINT correctly, runtime network none, read-only source bind, separate output bind, non-root `65534:65534`, requested `--cpus 1 --memory 512M`. It ran 2026-10-04 01:14:22–01:15:37 UTC (75.2s wall). WSLc warned: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” These flags do not establish enforcement or resource benefit.

## Result

`result.json`: FAIL. 205 tests ran. Protocol suite returned 0 (duration 63.18s); harness suite returned 1 (11.33s), with exactly two errors. Both are `FileNotFoundError: [Errno 2] No such file or directory: 'git'` in distribution-v2 tests that invoke Git. The other 203 tests passed. No suite retry was made.

Independent audit rehashed all 2,144 sources (zero mismatches), compared all four recorded log SHA-256 values to the saved logs (all matched), confirmed the two Git errors and suite statuses. Audit disposition: `AUDIT_MATCHES_SETUP_FAILURE`. This is test-image dependency incompleteness, not product failure. The next experiment is #7361, which will add a pinned Git executable only to a fresh ephemeral test image.

## Scope limits

No Docker Desktop comparison, speed or memory improvement claim, live GUI/model result, product-failure claim, or full roadmap-completion claim. A02's earlier build succeeded but its candidate command stopped at argument parsing; that result is preserved separately in #7342.