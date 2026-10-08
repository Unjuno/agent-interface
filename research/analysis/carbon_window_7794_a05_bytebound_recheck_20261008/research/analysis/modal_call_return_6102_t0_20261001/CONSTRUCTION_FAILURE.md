# Construction audit failure — preserved, not pooled

The first pre-freeze container construction candidate emitted all 14 raw traces. Its independent auditor then exited nonzero with `FAIL_AUDIT`: ten `fsm_mismatch` errors. The mismatch was in the auditor's expected JSON shape for rejected FSM rows: it omitted the candidate's `transitions` count. The independent disposition itself was correct; candidate code and raw input were not changed to conceal the discrepancy.

Retained exact artifacts:

- `construction_raw_initial.jsonl` — first construction raw, SHA-256 `de20f22b34d75751fbcc582053db35f2c0414b61bd909c96978af1820e1a1bc1`.
- `construction_audit_initial.json` — first failed auditor output, SHA-256 `d25505252aafa472c09473d063ced7ec19ddab5e811e9b24f859efedd16ed119`.

After correcting the auditor's output contract, a separate pre-freeze construction run passed: `construction_raw.jsonl` and `construction_audit.json`. Candidate, auditor and tests were then frozen. The initial mismatch is not counted as a scientific FAIL or a formal candidate result; it remains a construction/tooling failure disclosure.
