# Post-run auditor corruption controls

After the frozen A01 candidate and independent audit had completed, three
black-box controls were added to check that the raw-only auditor rejects
corrupted evidence. They are not part of the frozen scientific decision rule
and do not change, overwrite, or rerun the candidate. Each test invokes the
auditor on a temporary modified copy of the retained raw JSON and checks that
the process fails before it can write an audit result.

| Mutation | Expected rejection |
|---|---|
| Change the first span's trigger health | `raw span transcription mismatch` |
| Change the first effective hard floor | `sweep outcome mismatch` |
| Remove the last threshold row | `sweep outcome mismatch` |

Command, from repository root:

```powershell
python -B -m unittest research.doom.v28_health_envelope_counterfactual_a01_20261005.test_audit -v
```

Observed on Python 3.11.9: 3/3 corruption controls pass. These tests support
auditor tamper-detection for the named mutations; they do not make the replay a
live-control result or broaden its scientific scope.
