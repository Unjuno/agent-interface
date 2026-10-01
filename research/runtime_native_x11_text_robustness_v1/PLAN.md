# Plan — native X11 sub-ms text robustness v1

Dependency: retained compiled tight-loop text-pacing source/result from PR #145. Existing namespaces remain read-only.

Development with precise bounded monotonic busy-wait recovered sub-ms discrimination but showed non-monotonic single-session outcomes near 1 ms. Formal therefore tests repeated fresh sessions rather than declaring a single-run threshold.

Conditions: requested post-character delays 0.8, 0.9, 1.0, 1.1 ms. Five fresh private Xvfb/Openbox/LibreOffice Calc/XLSX sessions per condition (20 total), same fixed 16 repeated-character strings and separate post-execution openpyxl scorer. Every session must retain stale-observation zero-input and terminal-release receipts.

Fixed counterbalanced schedule:
R1: 0.8, 0.9, 1.0, 1.1
R2: 1.1, 1.0, 0.9, 0.8
R3: 0.9, 1.1, 0.8, 1.0
R4: 1.0, 0.8, 1.1, 0.9
R5: 1.1, 0.9, 1.0, 0.8

All 20 sessions execute once regardless of earlier failures. `ROBUST_CANDIDATE` is the lowest requested delay with 5/5 eligible exact sessions and all controls. This is an engineering promotion gate, not a statistical reliability guarantee. If none reach 5/5, HOLD. Requested delay and measured character-start interval are reported separately.

Implementation closure: a deterministic builder verifies the exact PR #145 dependency blobs, changes only the retained `time.Sleep(textPacing)` block to a bounded monotonic busy-wait, verifies the generated backend Git blob, runs Go tests, and builds the controller with `-trimpath`. The PR #145 runner/scorer are reused read-only.
