# Postformal audit repair

The frozen formal allocation itself completed18/18 rows and was not rerun. The original frozen `audit.py` returned `errors=[]` but only7/8 corruption controls: its `timestamp` mutation targeted `rows[-1]`, which was the late-control row in the six-case construction order but not in the 18-case cyclic formal order. Therefore the first formal disposition is retained as `HOLD_AUDIT_CONTROL_INCOMPLETE`, not PASS.

`audit_v2.py` changes only the copied-evidence mutation selector: it locates the preregistered `LATE_SAME_PROCESS_B` row by scenario before mutating its B timestamp. Scientific reconstruction/check logic is byte-identical otherwise. It is a postformal read-only evidence audit, not preregistered source and not a formal rerun. On the immutable formal RAW it returns `errors=[]` and8/8 controls rejected.
