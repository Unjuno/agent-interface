# Evidence map — Issue #7802 T0

| Claim | Evidence | Independent check / limit |
|---|---|---|
| Source was frozen before formal execution | `PREREGISTRATION.md`, `FREEZE.json`, source commit `142ed4c653f8421610b2f230ec731963c5309b18` | SHA-256 for every input and program is retained; fixture is authored, not host-derived |
| Candidate emitted all fixture images | `results/candidate-output.json`, `RUN.json` | 31 rows, candidate invoked once, exit 0 |
| Recovery labels preserve uncertainty | Candidate raw rows and `fixture.json` | `auditor.py` independently reconstructs each row; no receipt-only completion |
| Machine-crash state set differs from process-crash controls | `results/audit.json` | Three distinct machine-only state tuples in the authored finite model only |
| Mutation controls exercise audit sensitivity | `results/audit.json` | Four mutations rejected; construction suite also checks forged classification rejection |
| Formal run was one-shot | `RUN.json` and stdout/stderr receipts | Candidate 1, auditor 1, retries 0; no runtime/host crash operation |

This evidence does not establish a real filesystem's persistence guarantees, the behavior of any production journal, or T1 host-stack results.
