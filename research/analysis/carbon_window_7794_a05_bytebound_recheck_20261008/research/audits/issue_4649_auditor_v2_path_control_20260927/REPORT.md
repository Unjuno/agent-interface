# Issue #4649 — auditor-v2 symlink confinement control

## H / T / D / C / U

- **H:** v2's lexical `..` check might not confine reads when an in-root relative path is a symlink to a file outside the input root.
- **T:** One frozen, local Docker invocation of the exact PR #4672 `audit_v2.py` source against two synthetic disposable fixtures. A stub v1 PASS isolates v2's ledger/path logic. The old formal runner and eight-control harness were not invoked.
- **D:** Scoped PASS required both `../` and an out-of-root symlink to be rejected with structured errors and empty stderr. Result: **FAIL_SYMLINK_PATH_CONFINEMENT**. `../outside/sentinel` was rejected (exit 1, three structured errors); `linked-input` symlinked to `outside/sentinel` was read and returned `PASS_INDEPENDENT` (exit 0, no errors). Overall probe exit was 1 and was not retried.
- **C:** v2 source is PR #4672 head `0b7b3ceb70176da1e1a9f73d3cf228be280472ec`, SHA-256 `500946223763825cd7773dacae55ab67cc3b624b958c941fdd84b2b877f73630`. Docker Desktop 28.5.1; pinned cached image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, CPython 3.12.14. Network disabled, pull disabled, read-only root and source, 256 MiB memory, one CPU, 32 PIDs. A separate Docker process independently checked frozen source/result hashes and the preserved FAIL.
- **U:** Synthetic unit-level v2 ledger-check only; the v1 auditor is a deliberate PASS stub. This is not an execution of the prior eight controls, a re-audit of formal01, or evidence that #4649's underlying bytes changed. It identifies a path-confinement gap if symlinks are within the threat model. It makes no production/runtime claim and does not change the predecessor's `FAIL_AUDITOR_ROBUSTNESS`.

## Reproduction and retained evidence

Run from a clean checkout with the pinned image already available:

```sh
out="$(mktemp -d)"
docker run --rm --pull=never --network none --cpus=1 --memory=256m --pids-limit=32 --read-only \
  -e EXPECTED_IMAGE_ID=sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  -v "$PWD/research/audits/issue_4649_auditor_v2_path_control_20260927/source:/study:ro" \
  -v "$PWD/research/audits/issue_4649_auditor_v2_path_control_20260927/probe.py:/probe.py:ro" \
  -v "$out:/out:rw" \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python -B /probe.py
```

The command is expected to exit 1 because the symlink control is accepted. The first-run JSON and invocation receipt are preserved under `results/formal01/`; the independent audit under `results/independent_audit/` returned `PASS_INDEPENDENT_AUDIT_OF_RETAINED_FAIL` with zero errors. The exact tested v2 source is copied byte-for-byte under `source/` and its SHA-256 is frozen.

Prior results, including #4649's formal failure and #4672's eight controls, remain unchanged. This is an additive new control only. Do not interpret the independent evidence-integrity PASS as a scientific/path-safety PASS.
