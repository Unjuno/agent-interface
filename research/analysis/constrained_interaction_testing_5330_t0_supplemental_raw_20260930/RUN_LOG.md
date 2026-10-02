# Immutable run log — Issue #5330 T0

Base main: 1a27aff369ad1f690d4df6dc1664226ecc0726bb
Branch: research/constrained-interaction-5330-t0-20260930
Freeze commit: d92545c876aa87afc1c01393f98d389a28a68742
Execution date: 2026-09-30 UTC

## Candidate invocation 01
Runtime: one isolated JavaScript V8 functions.exec evaluation of the exact GitHub-read-back candidate.js, after freeze. Exit: complete; elapsed 389 ms. No filesystem, network, model, GUI, GPU/CUDA, container, live-system, or external-effect calls. Candidate raw is retained byte-for-byte as raw.json (127,088 UTF-8 bytes); SHA-256 ad6be24a2bd8789ffae8c9ef632c829c47813dab6477be6a324dd3c77363fec4. No candidate retry.

Observed: 1,024 total assignments, 640 valid; constrained pairwise 179 feasible patterns/9 rows; constrained three-way 942 patterns/20 rows. One-factor-at-a-time discovered 0/5 faults; pairwise 4/5; three-way 5/5; fixed-seed unconstrained random 3/5 with 10/20 invalid assignments. Strength escalation used 33 unique runs and found 5/5; 15 failing observations produced recorded deletion-minimization probes. Metamorphic checks: 27/27.

## Frozen audit invocation 01
The frozen auditor ran once and returned STOP_AUDIT_EXCEPTION: Error: metamorphic counts. The cause was its fixed expectation of 36 metamorphic rows; the frozen candidate correctly emitted 3 × 9 = 27 because the pairwise covering array contains nine rows. The STOP record is preserved unchanged as AUDIT_STOP_01.json.

## Separate corrected audit-only invocation 02
Only the auditor's metamorphic case-count expectation was changed to derive from the available pairwise row count. The exact candidate source and raw bytes were not changed or rerun. The separate raw-only audit completed in 1,788 ms: PASS_T0_SYNTHETIC_DESIGN, 1,024 assignments/640 valid, 179/179 pairwise patterns, 942/942 three-way patterns, 27/27 metamorphic cases, and 4/4 corruption controls rejected. Corrected auditor SHA-256: 5e9245ef61bc6abfd135ba89d78367cffb70bdb0357b8b365360353da26649da. See audit_corrected.js and audit.json.
