# Calc G10 to current-main public adapter crosswalk (2026-11-04)

## Decision

The retained G10 live route and the current registered public Calc route are
not the same experiment and should not be joined as one matched arm. Current
main already has an offline adapter composition from the public Calc prepare
tool through the owned compiled call, verified close, and a separate saved-file
scorer. No second adapter implementation is justified by the archived G10
packet. The remaining Issue #57 boundary is a fresh, prospectively frozen live
provider comparison, after the required offline matrix and allocation checks;
this audit does not authorize a replay or allocation.

## What G10 actually established

The retained source and run are under
[`calc_current_shared_3311_4d74_20261004/calc-compiled-ocrlive-4d74`](../calc_current_shared_3311_4d74_20261004/calc-compiled-ocrlive-4d74/REPORT.md).
The report and `runs/compiled_ocrlive10/raw.json` identify a real Calc/Xvfb
execution with two graph transitions, three capture-time-bound observations,
and seven retained Tesseract attempts (including the initial blank read). The
two tasks saved 29×31=899 and 43×47=2021; the separate saved-XML oracle checked
the expected values, formulas, and populated-cell set. Two native release
receipts were verified and final physical state was neutral. The raw compiled
receipt says `outcome=TASK_SUCCEEDED`; the report also warns that some inherited
top-level labels and plan prose are stale, so those labels must not replace the
structured outcome and the report's limitations.
The read-only extracted counts and exact retained OCR outputs are summarized
in [`g10-live-summary.json`](calc-g10-adapter-audit-20261104-01/g10-live-summary.json);
source blob IDs and comparison counts are in that packet's `source-diff.txt`.

That is positive, narrow live Calc evidence. It is not a provider-accounted
three-arm comparison: primary token usage is UNKNOWN, and its callbacks are
assembled directly around `NativeHandleBridge` in the retained OCR driver. The
historical runtime snapshot is source main
`9823419dc71eb6f7fd745bfe8249cf7f7584a3a9`, not current main.

## Contract mapping

| Contract | Retained G10 path | Current main and evidence | Remaining boundary |
| --- | --- | --- | --- |
| Task and target | A G10-specific two-save arithmetic task, pixel/OCR anchors, and values 29/31 then 43/47. | Registered `calc-ocr-save-v1` validates bounded cell values, binds a task plan to a fresh target, and keeps the current selected 731/864 two-cell task schema. | Different task artifacts and scoring contracts; G10 values/results are not samples of the selected workload. |
| Observation and freshness | Direct graph callback returns sequence, original `capture_started_ns`, source digest/reference, and OCR predicate. | `CalcPrimaryProfile` supplies current guarded observations, OCR dependencies, and capture-bound evidence; the public owned caller rechecks target generations and refuses stale admissions. | Current public/provider test uses Fake App Server and Fake X; it does not prove a live provider-to-Calc call. |
| Input and release | G10 executes through its hand-wired `NativeHandleBridge` graph callbacks; two execution receipts plus physical readback show verified release. | `mcp_server.py` prepares and consumes a call-bound `CalcTaskArtifact`; the owned compiled route returns method/release receipts; task verification requires verified close and exact target exit. | G10's release is not a release receipt for the current public caller or a cancellation/recovery trial. |
| Task effect | The G10-specific saved-XML oracle checks two input rows, the formula cell, and exact populated-cell set. | `CalcTaskArtifact` binds a Save request to call/attempt/process/window generations and scores the current task's saved FODS after verified close. | The current scorer intentionally does not accept the G10 three-row/formula workbook as the current two-cell task. Do not translate G10's positive score into the selected workload. |
| Provider/accounting | The packet retains primary request/graph events, OCR attempts and native receipts; primary model token usage is UNKNOWN. | The current Fake App Server composition joins synthetic attempts to public MCP calls, including failed/stale attempts and a fresh attempt. | Real provider raw/token accounting, all-attempt live lifecycle cost, and matched cold/warm/invalidation/repair economics remain open. |
| Source compatibility | G10 captured old `compiled_gui.py`, `guarded_x11_v1/bridge.py`, and `backends/x11_v1/session.py`. | Current main adds cancellation, task-artifact, public-call, and verifier boundaries; `guarded_x11_v1/frames.py` and `backends/x11_v1/capture_artifacts.py` remain byte-identical to the archived copies. | Do not transplant the old driver or infer current-main behavior from its source snapshot. Use the present public path for any future comparison. |

Source comparison confirms the version boundary: relative to G10's captured
copies, current `compiled_gui.py` has 224 added / 49 removed lines,
`guarded_x11_v1/bridge.py` 489 / 85, and `backends/x11_v1/session.py` 43 / 9.
The captured `guarded_x11_v1/frames.py` and
`backends/x11_v1/capture_artifacts.py` match current main byte-for-byte. The
G10 packet has no current public `mcp_server.py` route or provider-attempt
ledger, so its direct driver cannot stand in for that composition.

The current public seam is implemented in
[`mcp_server.py`](../../../runtime/cli_v1/mcp_server.py): Calc preparation
creates the server-owned artifact, compiled execution consumes it under the
same attempt, and `interface_verify_task` refuses to score without verified
close and target-exit custody. The current profile and scorer are
[`calc_profile_v1.py`](../../../runtime/guarded_x11_v1/calc_profile_v1.py)
and
[`calc_task_artifact_v1.py`](../../../runtime/guarded_x11_v1/calc_task_artifact_v1.py).
The synthetic provider-to-public-path join is
`test_calc_provider_wait_stale_refusal_then_one_fresh_attempt_releases` in
[`test_mcp_endpoint_composition.py`](../standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py).

## Rechecked current-main seam

On current main `bd5f574e8bfda33deca5117d6f2bd2709edd8016`, the complete
`test_mcp_endpoint_composition.py` module ran in the pinned network-disabled
Docker image with a read-only source mount, 2 CPUs, 4 GiB memory+swap, and 256
PIDs:

- Normal mode: 16/16 passed, 18.427 s.
- Optimized Python (`-O`): 16/16 passed, 18.248 s.
- Docker exit: 0.

The test also covers the synthetic provider wait, stale-source refusal, fresh
public Calc attempt, verified close, independently parsed task-owned FODS, and
a separate warm owner. This confirms the offline composition seam only; no
live Calc/provider call, task allocation, WSLc/MAP01 result, or efficiency
claim follows. Conditions, exact command, raw stdout, per-mode logs, exit
status, and hashes are retained in
[`calc-g10-adapter-audit-20261104-01`](calc-g10-adapter-audit-20261104-01/README.md).

## Next gate

Do not construct another adapter or replay G10. Freeze one current-main live
provider comparison around the registered public Calc route only after its
task values, model/settings, cold/warm/invalidation/repair arms, all-attempt
accounting, scoring, order, repetitions, budget, stop rule, and allocation
availability are independently checked. Preserve G10 as its separate
positive live OCR result and preserve the current synthetic composition as
offline evidence.
## Latest current-main composition rerun (2026-11-04)

After the previous 16/16 normal and optimized run at `bd5f574e8bfda33deca5117d6f2bd2709edd8016`, the same existing module was rerun on the then-current main commit `27c9814890ff753e632274658c35639b58ceb9e9` using the same pinned network-disabled image and resource limits. It again passed 16/16 in both modes (20.473 s normal, 23.187 s optimized). The raw packet is [`current-main-composition-rerun-20261104-01`](current-main-composition-rerun-20261104-01/README.md). This closes the source-revision freshness gap for the offline seam only; it does not change the live/provider or efficiency limitations above.
