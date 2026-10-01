# Allocation STOP-01 — Issue #3793

**Disposition:** `STOP_SOURCE_OR_FREEZE_MISMATCH`  
**Allocation:** `issue3711-downstream-truncation-audit-v3-01`  
**GitHub Actions run:** [35534995914](https://github.com/Unjuno/agent-interface/actions/runs/35534995914)  
**Workflow source commit:** `a6b79798eb3f35eb3b7c42c4f2028cfa25a8be34`  
**Frozen evidence commit:** `8bac49525c93835a69b6d441740a1c424faaecb2`

The GitHub-hosted runner was Ubuntu 24.04 ARM64. Docker Engine 28.0.4 successfully pulled and ran `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` as linux/arm64 with `--network none`, read-only source/evidence mounts, and a fresh output directory.

The frozen input check stopped on `INPUT_SHA256_MISMATCH:audit_plan`. The manifest expected `79741322f5c4b43d7d6a5a7b847bf3505bf94d2bc2f486ff27e405925dd795`; the exact plan bytes at the frozen commit hash to `79741322f5c4b43d7d6a5a7b847bf3505bf94d2bc2f486ff27e40592515dd795`. The expected value omitted `15`.

**Interpretation:** source/freeze mismatch STOP only. Baseline was not run. Although the first auditor version emitted preliminary mutation fields after detecting the source mismatch, this violated the required fail-fast gate; those fields are preserved verbatim in `STOP-01.stdout.jsonl` but are not admissible as mutation evidence. No `PASS` or scientific `FAIL` is claimed.

One audit container invocation occurred; zero formal experiment invocations occurred. This allocation is consumed and must not be retried. Any corrected audit requires a distinct successor allocation with a separately frozen source and a source mismatch gate that exits before any baseline or mutation work.
