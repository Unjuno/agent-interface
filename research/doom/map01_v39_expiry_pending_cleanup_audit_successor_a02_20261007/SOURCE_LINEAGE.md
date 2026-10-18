# Source lineage and rescue qualification

- Source pull request: #8257; source branch: `research/59-expiry-receipt-audit-v2-a01-20261007`.
- Source head: `fb466ea5dde34632fe977e9457078053de016b82`; source base: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- The 11 files in this package were byte-identical to the source-branch package before this lineage record was added. The package's 10 `SHA256SUMS.txt` entries verify.
- Rescue validation reran the recorded baseline mutation gate against the merged A01 auditor: the same three metadata mutations were accepted in both interpreter modes. The corrected auditor then passed all 11 test cases (22 isolated auditor subprocesses), accepting the unchanged A01 raw and rejecting all ten negative controls. A direct audit of that retained raw passed.
- The A01 candidate/raw was not regenerated or modified. No candidate, container, model, GUI, OS-input, game, or live-control experiment was run. This is an offline auditor correction only and does not establish physical release or resolve Issue #59's live-control gate.
- Source PR #8257 was a draft with no review submissions at intake. This rescue preserves its additive evidence on current main; it does not rewrite the predecessor result or claim a new candidate result.
