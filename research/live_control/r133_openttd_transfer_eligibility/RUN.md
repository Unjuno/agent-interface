# Run record

Host-only allocation OPENTTD-R133-EFFECT-JOIN-20261001-01

- Owner: Windows local Codex task 01a0b990-3d17-72f1-a908-9a2072104ce5.
- Start/end: 2026-10-01 14:50:32–14:50:58 UTC.
- Frozen main source base: b63fe0812e5816163105bdf37384c5f1dd407760.
- Python: CPython 3.11.9 on Windows.
- Input bytes were fetched read-only from raw.githubusercontent.com at the frozen
  main SHA. Their SHA-256 values are in README.md and embedded in both programs.

## Construction

Revision 1 ran the five corruption controls once: 4/5 passed; fabricated
button-up was not rejected. Candidate=0, independent auditor=0. This failed
construction is retained in README.md and branch history.

Revision 2 added the exact 7-down/0-up source-coverage invariant to both
programs. Command:

    $env:R133_AUDIT_INPUTS = Join-Path $env:TEMP 'r133-openttd-audit-20261001'
    py -3 -m unittest discover -s research/r133_openttd_transfer_eligibility -p 'test_audit.py' -v

Outcome: exit 0, 5/5 controls passed (dropped event, fabricated button-up,
wrong terminal identity, unverified release, non-neutral release).

## Candidate — one invocation

    $d = Join-Path $env:TEMP 'r133-openttd-audit-20261001'
    $o = Join-Path $d 'candidate-result.json'
    py -3 research/r133_openttd_transfer_eligibility/audit.py --events (Join-Path $d 'events.jsonl') --observer-log (Join-Path $d 'game-stderr.txt') --posthoc (Join-Path $d 'posthoc-audit.json') --output $o

Exit 0. Local output SHA-256:
3b3126c30dfaa1e6e1c7e8a6b0dd82aa2872787e45108a829388f16ca4987349

## Independent raw-only auditor — one invocation

Run only after the candidate exited 0:

    $d = Join-Path $env:TEMP 'r133-openttd-audit-20261001'
    $o = Join-Path $d 'independent-audit.json'
    py -3 research/r133_openttd_transfer_eligibility/independent_audit.py --events (Join-Path $d 'events.jsonl') --observer-log (Join-Path $d 'game-stderr.txt') --posthoc (Join-Path $d 'posthoc-audit.json') --candidate (Join-Path $d 'candidate-result.json') --output $o

Exit 0; status PASS_RAW_AUDIT_OF_HOLD_CLASSIFICATION. Local output SHA-256:
f7053023be0422c0837ccea827ddef691d000a35b0c847ba7520c2697edab773

The raw audit independently reconstructed all 311 runtime rows, all seven
down-to-neutral joins, the 263 observer records, first transition at record
91, and zero shared clock/identity keys. Retries=0.

