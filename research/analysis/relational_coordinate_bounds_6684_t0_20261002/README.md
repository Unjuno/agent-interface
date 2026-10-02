# Relational coordinate bounds — Issue #6684 T0

**Status: construction/audit tests PASS; formal WSLc run not yet performed.**

This finite, authored fixture compares independent coordinate interval boxes, relational difference bounds (DBM), and exact enumeration. It does not exercise a GUI or establish application safety.

## Reproduce construction checks

```powershell
python -m unittest -v test_construction.py
python candidate.py fixture.json raw.json
python audit.py fixture.json truth.json raw.json audit.json
```

The audit implementation does not import the candidate. It independently enumerates states, checks every claimed DBM bound contains each concrete difference, verifies the frozen truth table and case roster, and rejects false admissions. Construction unit tests inject a false admission, remove a row, and forge a concrete state to check rejection.

## Current result boundary

The finite construction shows the intended contrast in its authored cases: common-mode safe states can be admitted relationally where the independent box is UNKNOWN; the unsafe and independent-shift controls are refused. This remains pre-formal evidence until exact source/runtime/container identities are frozen and the one-shot WSLc candidate and separate audit executions finish. Requested memory flags are not evidence of an enforced limit.
