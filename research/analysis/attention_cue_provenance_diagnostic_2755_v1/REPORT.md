# Issue #2755 — deterministic attention-cue provenance diagnostic rung

## Disposition

**HOLD_AUDIT_CONTROL_ESCAPE**. The preregistered PASS is not awarded.

Allocation-01 stopped before rows because the launcher used Python isolated mode and could not import adjacent frozen modules. It remains `STOP_FORMAL_IMPORT_ISOLATION`, rows0, non-poolable.

Fresh allocation-02 changed only the launcher to ordinary `python -B` and completed the frozen 56-row matrix once. Mechanism metrics are favorable: CONTENT_ONLY unsafe trust 8, PROVENANCE 0, CORRUPTED_PROVENANCE 0, ORACLE 0; PROVENANCE valid target selections 4/4 and safe abstentions 8/8 with exact four-class attribution. Authority grants0. Raw SHA-256 `679757ba55d5f9ef36baf0fcc2fac73cffccd296d8509fd01a3a877ddd06f333`.

The frozen audit v1 did not satisfy the evidence-integrity gate: 7/8 corruption controls rejected, but its `truth` mutation escaped because the control checker did not bind the expected case-id→truth map. Audit v1 therefore returns `FAIL_ATTENTION_PROVENANCE_DIAGNOSTIC`. A separately labelled postformal read-only audit v2 binds the complete case/truth/arm matrix and reproduces the same mechanism metrics while rejecting 10/10 corruptions. V2 does not override the frozen audit or convert the overall disposition to PASS.

## H/T/D/C/U

- **H:** provenance bound to current frame/revision, detector/source role, observed-vs-inferred consistency, target/generation and task/action identity can reduce unsafe cue trust and improve failure attribution relative to content-only selection.
- **T:** 14 finite cases ×4 arms =56 rows: four valid target cues, two distractors, and two each of stale frame, wrong detector, inferred-as-observed and target-generation replacement. Standard-library deterministic scorer only; no model/GUI/input/network.
- **D:** frozen PASS required all mechanism gates plus independent audit and >=8 corruption controls. Mechanism gates passed; frozen audit integrity gate did not. Overall HOLD.
- **C:** defects are deliberately identifiable from declared metadata/current context. CONTENT_ONLY is an authored weak comparator. This is not a learned-model evaluation.
- **U:** real-model utility, natural defect rates, latency/tokens, arbitrary GUI transfer, authenticity and production security remain open.

## Execution/accounting

- source-first capsule Git blob readback matched local `0faf2a36358738b4d6d8c110a6e62c2ab49c56bb` before formal; decoded source capsule SHA-256 `c765bfc47be6566adfb3a7d97320e712bd2b5a1d26ca4d2943fa909e3195ec06`.
- allocation-01: STOP before row generation, no retry/pooling.
- allocation-02: formal invocation1, reruns0, replacements0, tuning0.
- frozen audit v1 SHA-256 `5ee70918cc0a9de66345f9aa7c55ef21b4b7fd4e0e0b6cddebed8aff2f05ae0a`.
- postformal audit v2 SHA-256 `d9e426869393eca246c081ad8089f8162ccf79e700468e3e3b63733c24d76725`.
- audit v2 source SHA-256 `4690c249bd7b4df9525550de86f6077a5f4c8f056882a66b62895dfb2e022667`.

No component result is promoted to model/task/product success.
