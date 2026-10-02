# Construction-only log (not formal allocation output)

This log records test-driven implementation checks before the frozen allocation window. No formal candidate or formal auditor invocation occurred during construction.

1. The behavioral test was first run before `candidate.py` existed. It failed as expected because the candidate runner was absent. The runner was then authored.
2. The candidate construction test exposed an incorrect fixture selector lookup (`KeyError: match`). The candidate was corrected to use the frozen fixture's top-level selector fields; its output-collision guard was also checked to refuse an existing output while allowing creation of a new parent directory.
3. After the independent auditor was added, the candidate assertions passed but audit construction failed with `reconstruction_mismatch`. A direct field comparison localized the discrepancy to one-pass ranking in the ambiguous case: the auditor had not cross-multiplied the route-specific denominators. The independent reconstruction formula was corrected to compare score bounds using each route's denominator.
4. The complete construction test then passed 1/1. The independent auditor reconstructed all 288 rows, found no remaining differences, and rejected all five prespecified corruptions. This is a construction-only result and does not count as either formal invocation.

The immutable candidate/auditor/fixture/test hashes and formal start/end window are in `FREEZE.json`. Formal outputs, if created, belong only under `formal-output-01/` and must never overwrite these construction records.

