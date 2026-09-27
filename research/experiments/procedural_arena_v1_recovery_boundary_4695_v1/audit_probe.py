import json
from recovery_probe import rows
errors=[]
for row in rows:
    if row["movement_px"] <= 0: errors.append(f'{row["seed"]}: no relocation')
    if row["stale"]["success"] or row["stale"]["recovery_successes"] != 0: errors.append(f'{row["seed"]}: stale control accepted')
    if not row["reacquire"]["success"] or row["reacquire"]["recovery_successes"] != 1: errors.append(f'{row["seed"]}: reacquisition failed')
    if not row["reacquire"]["state_matches"]: errors.append(f'{row["seed"]}: state mismatch')
    if not row["oracle"]["success"] or row["oracle"]["recovery_successes"] != 1: errors.append(f'{row["seed"]}: oracle failed')
print(json.dumps({"audit":"PASS" if not errors else "FAIL","rows":len(rows),"errors":errors},sort_keys=True,separators=(",",":")))
if errors: raise SystemExit(1)
