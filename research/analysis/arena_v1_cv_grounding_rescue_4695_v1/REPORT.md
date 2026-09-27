# Arena v1 CV grounding rescue — local run report

## Status: HOLD (frozen auditor inconsistency)

The frozen candidate was executed once against all 12 preregistered panels in the pinned local Docker image. Candidate source, thresholds, inputs, and decision gates were not changed after freeze.

### Recorded measurements

- Candidate rows: 12; proposals: 6; abstentions: 6.
- Positive localization: 6/6; minimum independent IoU: 0.9633058984910837 (retained frame). The other five positive IoUs were 1.0.
- Controls: 6/6 abstained, including all three ambiguous multi-square panels.
- Retained source point `[920,640]` is out of the 720x520 frame; candidate proposal was `[550,418,604,472]`.
- Corruption controls: 5/5 rejected (wrong positive box, guessed absent, guessed ambiguous, dropped denominator row, altered input binding).
- Frozen independent auditor exit code: 1, with three `control_input_unexpected_unique_square` errors on the ambiguous multi-square panels. Its control check rejects any eligible square (`if found`) even though the preregistered control definition explicitly includes multiple-square ambiguity and the candidate correctly abstains on those rows. This inconsistency means the preregistered `zero errors` audit gate is not met. The run is therefore HOLD, not PASS; auditor code was not edited or rerun with a modified gate.

### Reproducibility

- Container: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261` (`linux/amd64`, Python 3.12, Pillow 10.2.0); CPU-only, no GPU, `--network none`, `--pull=never`, read-only root/source/inputs, writable output only.
- Protocol tests: 3/3 passed.
- Candidate output: `outputs/cv4695-predictions.json`, SHA-256 `fd7da113807c6f9f10e4fa276d17d1e2760f297aa1c4bea0689ae79efb2823d8`.
- Commands: `python -m unittest discover -s /src -p test_protocol.py -v`; `python /src/run_suite.py /data /out/cv4695-predictions.json`; `python /src/audit.py /data /out/cv4695-predictions.json`; `python /src/corruption_test.py /data /out/cv4695-predictions.json`.
- No model/provider request or input action occurred. No GPU was needed for this small fixed-pixel experiment.

### Scope

This supports only a deterministic, proposal-only orange-square extractor on this fixed high-contrast 12-panel suite. It does not establish semantic grounding, general visual robustness, real-app behavior, action safety, or model quality. The audit HOLD prevents promotion/integration as a verified result. A successor run needs a preregistered corrected independent auditor and a new allocation; this frozen record must remain unchanged.
