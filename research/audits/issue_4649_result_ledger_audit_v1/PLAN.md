# Issue #4665 — frozen bounded audit

## Lineage

Successor to #4649 / PR #4659 `FAIL_AUDITOR_ROBUSTNESS`. Preserve the predecessor allocation and auditor-v1 unchanged. The predecessor's 7,915-byte formal evidence ZIP is not present in its PR and is not present in this task workspace; this experiment does not recreate or adjudicate that missing output.

## H — hypothesis

An independently computed ten-role input ledger can accept an exact result envelope and reject a missing role, altered digest, wrong path, and malformed ledger. This directly tests the defect described in #4649: the predecessor auditor validated the frozen input ledger but did not bind the reported result's `input_sha256` ledger.

## T — one raw-only invocation

- Inputs: the ten immutable #4649 role files plus its MANIFEST.json. They are read-only and their expected SHA-256 values are pinned in `FREEZE.json`; roles and original repository paths remain in `audit_ledger.py`.
- Predecessor v1 source identity: PR #4659 head `093979823173a7810dd19b2f84ae80d851847bb1`, blob `0fa674422c14b89e26b659d44a79fa1f8ce0f39f`.
- Container: exact cached Python image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, network none, read-only root, read-only source and input mounts; only a fresh output directory writable. Docker Desktop Engine 28.5.1; CPython 3.12.14.
- Construction and synthetic tests are excluded. Formal allocation, #4649 runner, and #4649 v1 auditor invocations are zero. Exactly one invocation of the new independent ledger audit; no retries, tuning, package installs, model, GUI, user files, or remote compute.
- Retain exact stdout/stderr, exit code, AUDIT.json, input hashes, controls, image/runtime identity, and output hashes.

## D — gates

- `PASS_RESULT_LEDGER_BINDING_SCOPED`: all ten frozen input hashes and the manifest match; an exact result envelope passes with no errors; the three frozen mutations (drop row, change digest, wrong path) each return structured rejection with nonempty errors; no exception or stderr.
- `FAIL_RESULT_LEDGER_BINDING`: the exact envelope fails or any mutation is accepted.
- `STOP_PROVENANCE_OR_ENVIRONMENT`: any source, input, image, or execution identity fails before semantic audit. Do not retry.

## C / U

Corruptions change only copied result metadata, never input bytes. This tests a finite synthetic result envelope and one local amd64 container. It cannot recover or re-audit #4649's unpublished ZIP, change the prior FAIL, reproduce ARM64, or establish CLI/runtime/production/product behavior.
