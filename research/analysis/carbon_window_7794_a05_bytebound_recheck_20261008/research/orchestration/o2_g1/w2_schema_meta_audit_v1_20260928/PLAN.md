# W2 JSON Schema meta-validation successor — 2026-09-28

Parent evidence: Issue #60 O2 W2 result comment and merged PR #4904. This is an additive audit/conformance check, not a Worker-return acceptance or permission to activate W3/W4/formal work.

## H/T/D/C/U

- **H:** The W2 event-schema.json is a valid JSON Schema Draft 2020-12 schema, and all eight frozen synthetic trace envelopes validate against it using an independent standards implementation. Invalid schema mutations and invalid instance mutations must be rejected.
- **T:** One offline CPU Docker audit against current-main snapshot 8a56d66e2e6951081469a9ecbfc4e047d13d53af. Exact source Git blobs: schema ebc424d2df631aa74c6d9aee4699c595a27ed589 / SHA-256 3ca91926d9e362e02dd0272a03b67e2d65b46199bcfb1bb8f55c29cfe92f6d76; cases 0a49a00567c25766495cd332be50f6c2946781f7 / SHA-256 6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f. The audit uses jsonschema==4.25.1, downloaded as six pinned Linux/amd64 wheels and installed from a read-only wheelhouse; no package/network access occurs in the container. Auditor SHA-256 ca3b0a627faf6a3878af5eeaf85c01f6640a11d65413156008578d7649372ac0. Base image python:3.12-slim, ID sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 (linux/amd64). Limits: network none, read-only root and source/wheelhouse, 0.25 CPU, 256 MiB, 32 PIDs, dropped caps, no-new-privileges, tmpfs-only installation/output mount.
- **D:** PASS only if Draft202012Validator.check_schema accepts the exact frozen schema, all eight transformed trace envelopes validate, seven invalid schema mutations fail meta-validation, and seven invalid data mutations fail instance validation. Any mismatch is retained as FAIL/HOLD; no retry under this one-shot audit ID.
- **C:** Independent standards-library conformance, not the existing W2 custom verifier/auditor. It checks schema meta-validity and example-instance validity only; W2 semantic chronology/authority invariants remain separate.
- **U:** No cross-clock calibration, live physical occupancy, independent useful effect, recovery efficacy, model/GUI/input/runtime evidence, external Worker return, inherited lease inventory, or Gate-1 completion. This result cannot authorize W3/W4 or a formal allocation.

## Frozen wheel SHA-256

- attrs-26.1.0-py3-none-any.whl: c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309
- jsonschema-4.25.1-py3-none-any.whl: 3fba0169e345c7175110351d456342c364814cfcf3b964ba4587f22915230a63
- jsonschema_specifications-2025.9.1-py3-none-any.whl: 98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe
- referencing-0.37.0-py3-none-any.whl: 381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231
- rpds_py-2026.6.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl: ecabd69db66de867690f9797f2f8fa27ba501bbc24540cbdbdc649cd15888ba6
- typing_extensions-4.16.0-py3-none-any.whl: 481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8
