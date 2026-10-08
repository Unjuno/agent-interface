# Issue #8528 — finite decision-opportunity regret T0

This package tests one narrow method claim: evidence age alone cannot determine decision quality while a decision opportunity remains open. Two cases expose byte-identical candidate-visible rows and identical evidence-age sequences (3, 4, 5), tie on the age-only sum (12) and toy unsafe-exposure duration (0), while audit-only finite truth yields integrated toy regret 0 versus 3.

This is synthetic method evidence only. The toy 0/1 loss is an exact finite fixture convention, not user or task utility. No agent, model, GUI, human, network service, or runtime behavior is changed. No causal effect is inferred. No Docker/WSL boundary is needed for this deterministic sub-second calculation.

## Contents

- `visible.json`: frozen candidate-visible finite cases.
- `truth.json`: audit-only exact state/loss oracle, toy unsafe-exposure comparator, and hard-safety control; never passed to the candidate.
- `candidate.py`: deterministic candidate that emits decision rows and evidence age.
- `audit.py`: separate exact enumerator; does not import or execute candidate code.
- `test_candidate.py`, `test_audit.py`: construction tests; not formal-run counts.
- `PROTOCOL.md`: frozen hypotheses, gates, and run order.
- `CONSTRUCTION_LOG.md`: chronological development/test history.

## Local reproduction

Run from this directory with Python 3.12 or compatible:

```powershell
python -B -m unittest -v test_candidate.py
python -B -m unittest -v test_audit.py
python -B candidate.py --dir .
python -B audit.py --dir .
```

The formal candidate and auditor invocations are one each, only after the exact committed pre-registration sources have been read back and blob-hash checked. Construction runs above do not count as formal invocations.
