# Relational coordinate bounds — Issue #6684 T0

**Status: construction/audit tests PASS; formal WSLc run STOP/INFRA before candidate execution.**

This finite, authored fixture compares independent coordinate interval boxes, relational difference bounds (DBM), and exact enumeration. It does not exercise a GUI or establish application safety.

## Reproduce construction checks

```powershell
python -m unittest -v test_construction.py
python candidate.py fixture.json raw.json
python audit.py fixture.json truth.json raw.json audit.json
```

The audit implementation does not import the candidate. It independently enumerates states, checks every claimed DBM bound contains each concrete difference, verifies the frozen truth table and case roster, and rejects false admissions. Construction unit tests inject a false admission, remove a row, and forge a concrete state to check rejection.

## Current result boundary

The finite construction shows the intended contrast in its authored cases: common-mode safe states can be admitted relationally where the independent box is UNKNOWN; the unsafe and independent-shift controls are refused. The candidate was not executed in WSLc: the default-session image inventory produced no usable image identity; fresh named-session and isolated-session attempts returned `WSLC_E_SESSION_NOT_FOUND` and `ERROR_FILE_NOT_FOUND`. No existing session was reused or altered; no image was pulled and no host run was relabelled as formal. There is no WSLc runtime result or verified image digest, so the method remains pre-formal. Requested memory flags are not evidence of an enforced limit.
