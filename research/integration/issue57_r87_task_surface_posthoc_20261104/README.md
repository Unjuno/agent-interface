# r87 task-surface crop posthoc analysis

This read-only analysis uses only the retained r87 observation 13 and 18 PNGs.
It checks their original SHA-256 values against the corrected custody manifest,
compares the whole image, then reports one fixed candidate crop for a future
prospective observation gate.

Run from the repository root with Pillow installed:

```powershell
python research/integration/issue57_r87_task_surface_posthoc_20261104/audit_task_surface.py
```

The current result is in `AUDIT.json`.

## Result

The retained full-frame images differ at 591 of 1,024,000 pixels, preserving
r87's original `FAIL_OR_UNKNOWN` outcome. The initial exploratory crop
`(left=0, top=126, right=1219, bottom=742)` includes Calc's visible row/column
headers and spreadsheet cell canvas. It differs at five pixels, all in column
`x=1218` along the right edge, where the vertical scrollbar begins. Moving the
right boundary inward by one pixel to `right=1218` removes those five pixels;
the resulting crop has zero changed pixels.

Both crop boundaries were selected after inspecting the mismatch. This is
therefore a posthoc candidate only: it does not validate an observation
contract, satisfy the frozen full-frame gate, or turn r87 into a pass. A future
run must freeze the crop, coordinate convention, task-surface content
assertions, and verifier timing before its first input. It must retain the
full-frame screenshots and independently verify the saved task artifact as
separate evidence.

The retained outer audit binds a FODS artifact hash and reports cells A1=731
and A2=864. The compiled result itself keeps `task_success` null and its task
effect verification unconfigured. This analysis does not strengthen that
receipt or establish provider usage, efficiency, WSLc, MAP01, or broad
reliability. The original r87 packet also remains short seven log files and an
exact copy of the frozen `experiment.py`; this report does not repair that
custody gap.
