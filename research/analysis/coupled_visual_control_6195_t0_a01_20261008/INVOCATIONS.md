# Formal one-shot invocation record

Source/freeze: [`FREEZE.json`](FREEZE.json), based on main `8d2eac460a7744d049bbca1d25b3cde86b1b496c`. Formal budget: one candidate, one independent auditor, zero retries.

| Role | Command | Count | Exit | Retained output |
|---|---|---:|---:|---|
| Candidate | `python candidate.py cases.json` | 1 | 0 | `CANDIDATE.stdout.json`; stderr `CANDIDATE.stderr.txt` |
| Independent auditor | `python audit.py cases.json CANDIDATE.stdout.json` | 1 | 0 | `AUDIT.stdout.json`; stderr `AUDIT.stderr.txt` |

Candidate and audit ran after freeze, sequentially, in the same local directory. Both stderr files are empty. The auditor reports `PASS_METHOD_SCOPED`, `audit_contract=PASS_AUDIT_SCOPED`, 8/8 reconstructed rows, 0 mismatches, 0 certified feature escapes, and 3/3 gain mutations rejected. No formal retries or post-run source edits occurred.

The 15-test construction suite ran once before freeze and is not counted as a formal candidate/auditor allocation. Earlier red/green API-contract test iterations occurred before freeze and are documented by the retained construction transcript. The exact frozen case suite was evaluated during pre-freeze construction tests; formal counts above distinguish those implementation checks from the frozen one-shot candidate and independent auditor commands, per the protocol's explicit separation.
