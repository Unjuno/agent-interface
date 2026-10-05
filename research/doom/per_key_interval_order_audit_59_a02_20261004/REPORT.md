# Independent verification of PR #7602 interval-order repair

## H/T/D/C/U

- **H:** The updated `input_edge_receipts` at PR #7602 head `40c6a278d06ec4411b72dd5d7d8899d85bebfcf4` rejects any pair whose sampling bounds do not prove strict DOWN-before-UP, while retaining strictly separated valid pairs.
- **T:** AST-extract the exact function from the source blob pinned below. Exercise ordered, touching, overlapping, and reversed synthetic pairs, then enumerate all 100 pairs of valid closed intervals with endpoints `{0,1,2,3}`. No runtime, game, model, or OS input is invoked.
- **D:** PASS only when the ordered pair remains `adapter_edge_brackets_paired`, the three ambiguous/reversed examples are `adapter_edge_receipt_incomplete`, all 15 strictly ordered enumerated pairs remain paired, and all 85 non-strict pairs are incomplete.
- **C:** A synthetic projection check validates source logic only. It does not show that a retained run was mismeasured or that the live bridge behaved this way.
- **U:** No live X11, physical key dwell, application consumption, task effect, threat control, or MAP01 outcome was tested.

## Result

**PASS: strict chronology fix verified.** The updated predicate requires `down_interval[1] < up_interval[0]`. The ordered synthetic case remains paired; touching, overlapping, and reversed cases are incomplete. Exhaustive enumeration classified all 15 strictly ordered pairs as paired and all 85 other pairs as incomplete. The independently extracted source matched PR blob `84cf5c5a812ae02f2bd454f35aab30becfd704e1` (SHA-256 `a6ec913551d5d9f40ab06bd2dd76b8e1730ff0f1b66a911fecd5927118aee813`).

This verifies the source-level projection contract and regression matrix only. The PR remains draft; no claim is made about PR acceptance, hosted checks, live input, or task success.

## Reproduction

From the repository root:

```powershell
python research/doom/per_key_interval_order_audit_59_a02_20261004/source/audit.py
```
