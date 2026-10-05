# #6526: retained publication bounds, HOLD preserved

The retained A02 trace supports **179 certified on-time publications, one certified late publication, zero unresolved intervals**. The existing descriptive 1/30 SENSITIVE/SCREENSHOT count is confirmed using a lower bound, rather than assuming a post-replacement reading is the effect's exact timestamp. This does not repair the independent deadline sampler: all180 samples were late, so **HOLD_AUDIT_TIMING / H_NOT_EVALUATED remains**. A01 STOP and the original A02/A03 artifacts are untouched. References #6526 and merged #6848.

This is an ordinary finite retrospective analytical construction, not another formal allocation. The author froze [the plan](PLAN.md) and code at `2026-10-03T03:43:14.193428+00:00`, before parsing all180 retained trials. It invokes none of the old candidates/auditors and no GUI, model, container, image, display or physical input. The logical result is conditional on the recorded fixture/clock order and concerns this action's file replacement, not first-ever presence or durable storage after power loss.

## Source reasoning and result

In the exact fixture, `action_ns` is sampled before temporary write and `os.replace`; `persisted_ns` is sampled after successful replacement. Call these L and U. The publication clock position is conservatively inside [L,U]. D is the nominal numeric monotonic deadline. U<=D certifies on-time; L>D certifies late; L<=D<U is unresolved. Merely observing U>D does not prove a miss. The possible-time negative control demonstrates both an on-time and late world with identical straddling endpoints.

Python documents successful POSIX [replacement atomicity](https://docs.python.org/3.12/library/os.html#os.replace) and [monotonic integer readings](https://docs.python.org/3.12/library/time.html#time.monotonic_ns). The interval is an inference from source ordering, not a measured linearization timestamp. The ns representation is not measured clock resolution. Snapshot_ns precedes exists/read, and a late positive snapshot cannot establish nominal-deadline presence. candidate.py uses mkdir(exist_ok=True), so it does not itself prove initially empty output or exclude external writers; no absence-based strengthening is used.

| Schedule / arm | On-time | Late | Unresolved | Identified miss-count bounds |
|---|---:|---:|---:|---:|
| SENSITIVE / MINIMAL | 30 | 0 | 0 | [0,0]/30 |
| SENSITIVE / SCREENSHOT | 29 | 1 | 0 | [1,1]/30 |
| SENSITIVE / SHAM | 30 | 0 | 0 | [0,0]/30 |
| STABLE / MINIMAL | 30 | 0 | 0 | [0,0]/30 |
| STABLE / SCREENSHOT | 30 | 0 | 0 | [0,0]/30 |
| STABLE / SHAM | 30 | 0 | 0 | [0,0]/30 |

For `b05-sensitive-screenshot`, D=`374733038529564`, L=`374733046091323`, U=`374733050899647` ns. L is already **7.561759 ms after D**; U is12.370083 ms after D; interval width4.808324 ms. Thus that action's publication is definitely late under the source-bound numeric cutoff. The late snapshot saw the expected payload12.428198 ms after D. The old endpoint classification happens to agree for this trace; its general point-timestamp justification remains insufficient for a straddling interval. No retained row straddles the deadline.

All180 snapshot lags are positive: min0.046112 ms, max46.349356 ms. No new sampling tolerance, effect threshold, p-value or causal claim is supplied. Identified count bounds are not statistical confidence intervals and do not override the failed punctuality gate.

## Custody and checks

[INPUTS.json](INPUTS.json) pins370 selected files by original path/mode/Git blob/size/SHA256 at main `332da58a9b6b825c384a142dfb59d7ed2b8b774e`. A02/A03 subtrees were unchanged at intake maina3e93e471 and final context maina96283ace. Export copied735,510 bytes without running source. The original SHA256SUMS matched all364 selected result/raw artifacts; original fixture/candidate and frozen trial-input hashes matched. The original tar archive is retained in main and was deliberately not exported/rehashed.

[interval-result.json](evidence/interval-result.json) records every row and all six cells. SHA256 `9bd9703e314912124031d3e0604f750f3ce8bdace16f91b8531ab01d6515d1f3` remains unchanged across validation.

- Finite possible-time oracle:196 fixtures, including equal endpoints/deadlines; upper-endpoint-as-point negative control.
- Producer controls:12 invalid type/JSON cases,18 retained-record corruptions and wrong-manifest digest rejected, normal and-O. All180 positive records accepted.
- Separate stdlib-only raw reconstruction:180/180 rows and six bounds agree; imports neither the producer nor original candidate/auditors.
- Actual private-copy custody controls:8 changed-input/manifest/path/mode/blob/size/source cases rejected.
- First result checker accepted3/7 corruptions (Boolean-zero alias, equal float reading, wrong top-level trial count). Original checker, raw control outcome and source pins remain preserved. [independent_check_v2.py](independent_check_v2.py) adds exact field types/count/status/summary checks; it rejects all7, normal and-O, without rerunning the producer. These are validation-construction failures, not new science trials.
- Public materializer round trip:370/370 exported files match input hashes. No whole-repository archive operation.

Original argv/UTC/exits/streams and hashes are in [commands.json](evidence/commands.json), [v2-commands.json](evidence/v2-commands.json) and the custody receipts. [CONTROL_PLAN.md](CONTROL_PLAN.md) records the separate post-result validation scope. [CONSTRUCTION_ATTEMPTS.md](CONSTRUCTION_ATTEMPTS.md) retains export/helper failures. [REDACTION.json](REDACTION.json) maps only local private-path substitutions to privately retained original bytes and hashes; source/data/clock/counts are untouched. The original unredacted freeze hash is `bc8469d96c2101fde4060a59a81f433d397808572cd8f64f7e2492ccc3d1a086`. Command freeze-hash fields refer to those original bytes, with the mapping explicitly retained. [MANIFEST.json](MANIFEST.json) covers published package bytes except itself.

## Reproduction

From repository root, let P denote this directory, I a new private input directory, and O a new result filename. Python3.11.9 stdlib was used; native event source remains the historical ARM64 Python/Tk run. Exported .py inputs are inert custody data and must not be imported/executed.

```text
python -B P/materialize_inputs.py . I
python -B P/intervals.py I P/INPUTS.json P/FREEZE.json O
python -B P/controls.py --inputs I --manifest P/INPUTS.json --freeze P/FREEZE.json
python -O -B P/controls.py --inputs I --manifest P/INPUTS.json --freeze P/FREEZE.json
python -B P/independent_check_v2.py I P/INPUTS.json P/FREEZE.json O
python -B P/custody_controls.py I P/INPUTS.json P/FREEZE.json O P/independent_check_v2.py
```

On a partial clone, materializer --prefetch fetches only the selected object IDs together. It does not change a branch ref. Without it, Git may fetch missing blobs individually. Source/tree binding and output-byte checks precede materialization; destination must be new. For v1 historical weakness reproduction, use independent_check.py only as the custody-controls last argument. The old checker is not the final acceptance oracle.

Scope remains recorded publication ordering in one synthetic fixture. No first-presence, filesystem-durability, observer-overhead prevalence, production deadline, GPU/model/input, physical release, permission, equivalence or efficiency result is established. Committee review and actual-current integration/apply conditions are separate; this package is not authority to merge or replay.
