# Hosted Native MCP evidence and local Node 22 run

The PR-head Native MCP v1 job succeeded on head `6faf147afcc5a7f72f2d79c8c39de1465279b196`: [workflow run 37165227376](https://github.com/Unjuno/agent-interface/actions/runs/37165227376). The job completed the persistent relay/primary Node tests, Python/native integration, and strict UTF-8 test. The runner's retained result reports protocol **445/445 PASS** and harness **205/205 PASS** on Ubuntu with Python 3.12.14; its runner hash matches `runtime/integration_checks/native.py` in the candidate. The hosted startup-close witness records `PRIMARY_OUTPUT_CLOSED`, no ready row, no exchange directory, and clean fixture/host exit.

The workflow artifact ID was `11288989350` (`native-contract-checks`, SHA-256 digest `dcf01f47a162f60336e6c3f6ccabf64fc035efff1ff5b39e89250135de40f27c`). The artifact's `native-ci/` result and complete logs plus `primary-owner/` witnesses are preserved under `run-37165227376/` so the evidence does not depend on the artifact's expiration window.

The exact 17-module Node command was also run locally on macOS with Node.js 22.23.3 and private inert fixtures: **211/211 PASS**, exit 0. The raw TAP log, empty stderr, invocation and receipt are retained under `node22-local/`. This local run complements the hosted job; neither result is an end-to-end computer-control or live GUI claim.
