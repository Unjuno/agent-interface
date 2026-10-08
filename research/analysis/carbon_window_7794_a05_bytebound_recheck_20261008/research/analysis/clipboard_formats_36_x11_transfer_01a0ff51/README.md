# Native X11 multi-format clipboard transfer for #36

Four fresh native transfers show the representation/effect distinction across
separate Qt owner and consumer processes. A matching text/plain payload can
coexist with a conflicting text/html payload that a rich widget pastes.
The plain widget follows the plain payload. This is a narrow transport result.

Read [REPORT.md](REPORT.md), [the prospective protocol](PREREGISTRATION.md),
[the freeze](formal/01/FREEZE.json), and
[the original independent raw-only audit](formal/01/audit/audit.json).
The candidate and auditor ran once each, with no formal retry. Original
construction failure and construction source snapshots remain under
`construction/`. No shared runtime or CI entry point imports this package.

To inspect retained evidence without pasting or invoking X11:

```sh
cd research/analysis/clipboard_formats_36_x11_transfer_01a0ff51
python3 -B -m unittest test_audit -v
python3 -B audit.py --cases cases.json --raw formal/01/run/raw.json --output /tmp/clipboard36-x11-fresh-audit.json
```

The audit output must be fresh. The second command is a supplemental retained
raw audit, never a rerun of the consumed formal candidate or formal auditor.
`run.py`, `app.py`, and `launch.py` are the preserved experiment, not a runtime
clipboard feature or an instruction to execute the consumed allocation again.

This study supplements the merged
[offscreen T0](../clipboard_formats_36_t0_01a0ff51/). It does not replace or
repair the evidence-incomplete consumed #3981 admission/mutation experiment.
