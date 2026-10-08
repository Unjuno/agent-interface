# A06 - Strict raw audit for the retained A05 output

This additive successor preserves every A05 file unchanged. PR #7633 review found that A05's raw-only auditor trusted candidate-controlled labels and total row count, so duplicate rows could hide omitted cases. A06 audits the already-retained bytes; it does not rerun or alter the A05 candidate.

The frozen input is copied byte-for-byte from A05 commit 690c460648917ca22ae14c92561c38e65677b30d. Expected SHA-256: 9506457a371565b489b5e1b9f7313c05d3f13a28bd5448b4b2944211ee4f313e.

The strict auditor reconstructs all five exact cases, event fields and A04/A05 dispositions, comparing types, keys, values and ordering. Nine mutations must be rejected: duplicate, omission, relabel, label/payload mismatch, altered kind, polarity, usefulness, disposition, extra row and bool/integer type confusion. A separate self-contained raw-only auditor independently reconstructs the contract without importing candidate or A06 auditor code.

Evidence is limited to retained synthetic JSON bytes and audit tamper-resistance. It says nothing about live scorer truth, runtime provenance, effect attribution, causal feedback, recovery, survival or gameplay efficacy. No model, game, GUI, OS input, GPU, live allocation or network is used. See RESULT.json, AUDIT.json, COMMANDS.md and FREEZE.json.
