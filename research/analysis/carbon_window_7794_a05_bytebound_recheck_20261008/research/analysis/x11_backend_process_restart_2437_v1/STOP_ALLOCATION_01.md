# Allocation 01 — pre-invocation STOP

- Allocation: `X11-BACKEND-PROCESS-RESTART-2437-20261001-01`
- Freeze branch: `research/2437-backend-process-restart-xvfb-20261001`
- Freeze commit: `1a9cd539c23e27e7458f75bc85b13968eb60f9bc`
- Frozen main: `d1dc9b8e6cc1e165d353f086b530a0024277b7f6`
- Launch-gate main: `d077494b50341f638e6d66f63e817ec48923768d`
- Disposition: **STOP_MAIN_ADVANCED_BEFORE_LAUNCH**
- Candidate invocation count: 0. Raw file: absent. Audit invocation count: 0.
- The exact output directory `/tmp/agent-interface-2437-backend-restart-d1dc9b8e-20261001` was verified absent at the launch gate.
- GitHub compare showed main advanced by one commit, `ci(native): omit nested research bundles from contract checkout (#5617)`, changing `.github/workflows/native-mcp-v1.yml`, `runtime/integration_checks/README.md`, and `runtime/results/native-ci-source-scope-01/**`. The five experiment dependency files retained identical SHA-256 values, but that does not waive the frozen exact-main gate.
- No Docker container, Xvfb candidate, backend worker, task input, raw or auditor was started for this allocation. The construction tests/preflight were separate and had completed before freeze.
- Allocation 01 is consumed as a provenance STOP and must never be rerun. Allocation 02 is a separately identified freeze on the newer main; results are not pooled.
