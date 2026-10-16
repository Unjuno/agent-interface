# A06 — trace sample audit with corrected baseline

A06 corrects A05's normal-case pre-sample expectation using the retained raw query/result pair. It independently reconstructs all 52 baseline checks and applies 12 frozen mutation controls. The single WSLc formal audit passed; candidate invocations: 0, auditor invocations: 1, retries: 0. See `RUN_RECORD.md`, `DISPOSITION.json`, and `formal/run1/RESULT_A06.json`.

The result establishes internal binding consistency in the immutable synthetic fake-X record only. It does not establish real X11 or physical input state, GUI/application effect, useful feedback, latency, recovery efficacy, live gameplay, or safety. Original A02 remains FAIL; prior A03/A04/A05 evidence and outcomes are retained without alteration.
