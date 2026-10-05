# Visual04 status-aware usage audit A01

## H / T / D / C / U

- **H:** The saved visual04 audit overstates completed-turn usage by summing all six `last` snapshots, including two interrupted turns whose notifications repeat the preceding completed snapshots. A status-aware summary can retain the four completed-turn snapshots while leaving both interrupted increments unknown.
- **T:** At frozen main `5ce152e1479bedac08f55db45d24b3dd1405cb16`, join all six report turn IDs to raw `thread/tokenUsage/updated` notifications. Classify from each decision's planner terminal status. Preserve the first auditor output; run a new candidate summary and a separate raw-only independent check.
- **D:** PASS scoped if the six IDs join one-to-one, four decisions are completed and two interrupted, the completed-turn `last` snapshot field sum is 48,773 input / 1,100 output, and both interrupted increments remain `UNKNOWN` regardless of snapshot equality.
- **C:** This checks evidence interpretation and record joining from the saved visual04 episode only. `last` and `total` remain descriptive fields; their exact accounting semantics are not inferred. The candidate never sums interrupted snapshots.
- **U:** No exact all-attempt cost, billing, controller caching defect, useful gameplay/recovery, causal benefit, physical key-up, or live-control claim is established.

The original `audit_visual_04.py`, `SAVED_READMISSION_AUDIT.json`, and `USAGE_QUALIFICATION.json` are unchanged. The original first-auditor sum of 71,597 input / 1,724 output is retained as its historical output and explicitly not adopted as a completed-turn result. The new field is named `completed_turn_last_snapshot_sum`; it is not labeled exact turn usage.

## Reproduction

From this directory:

```powershell
python -B -m unittest -v test_usage_audit.py
python -B run_audit.py
python -B audit_raw.py
```

The runner refuses to overwrite `out/a01`. `FREEZE.json` pins the original report, host notification stream, usage qualification, and first audit by SHA256. The independent checker does not import the candidate module. Both interrupted turn IDs have notifications that exactly repeat the preceding completed notification's `last` and `total` snapshots; the successor still reports both increments as `UNKNOWN`.
