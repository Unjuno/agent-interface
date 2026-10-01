# Emitted golden v3 → CLI mapping with source provenance (#2226)

## Result

**PASS_EMITTED_GOLDEN_V3_MAPPING_SCOPED**

Unlike prior synthetic contract fixtures, this audit uses the actual main artifact `runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json` (blob SHA `e168a9bdc84fc6b807f4e90806ec7c501da89689`). It validates:

- report schema `agent_interface_golden_desktop_live_v2`;
- six exact submissions and six independent evaluation records;
- no missing/unexpected/duplicate evaluation;
- all releases verified;
- zero old-target pointer admissions;
- repair task with missing old reference and successful repair;
- doctor schema passed;
- aggregate usage retained.

The read-only mapping emits `golden-v3-result-v1` with `task_success` sourced from independent evaluation, not launcher completion, and `authority_granted=false`.

Pinned related sources:
- frozen result schema: `7fe3ad10ab69b0d8786d17ca854e65f90efd213b`
- `runtime/cli_v1/api.py`: `5674bd39e3cb2170095f476dac90e2a781f4f77a`
- `runtime/cli_v1/receipt.py`: `ebe71a2edfbb524a4288241686b969342a0bfcae`
- `runtime/cli_v1/README.md`: `8cafa39718f0d5d66cb73adeb3aa99f0f1cce6d6`

Container: `python:3.12-slim`, py_compile plus one validator run.
Digest: `41714c968ad950f279168e0922d693d6aa79e0d1698787fa83baf0fa9a9ace2d`.
Counters: formal=1, model reruns=0, GUI reruns=0, input=0.

## Boundary

This is a read-only mapping of one retained run. It does not modify or rerun golden desktop, does not implement production runtime, and makes no generality, latency, token-efficiency, or human-tempo claim.
