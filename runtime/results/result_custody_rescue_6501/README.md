# Shared-result custody evidence rescue

Original source: `392c9dddba2ff022d3e7e217c37100892ea863f1`, remote branch
`research/6501-result-custody-01a0ff35-20261003-v2`.
The complete packet under
`research/concurrency/singleflight_result_custody_6501_01a0ff35` is restored
with exact Git bytes; staged comparison against the original exits 0.

Original Windows comparison covers 30 authored conditions, 60 deliveries and
35 producer entries. Its original scoped PASS is historical, not a fresh run.
The later repair documents that the original audit accepted A delivery before
producer return; all 30 directed A-before-return witnesses are retained with
the repair, original failures, CRLF preparation error and qualified first
optimized execution. Neither the original claim nor subsequent HOLD is erased.

The saved repair helper has author-workspace paths. Fresh normal and optimized
saved-record checks each pass 4/4 on macOS Python 3.14: original summary retained,
30 A-before-return copies rejected by V2 although accepted by V1, and 30 B copies
plus 60 typed call aliases rejected by both. Raw and witness pins are checked.
Only helper `here`, `package`, and target import path were rebound in a streamed
copy; no original file changed and no consumed producer/audit main executed.
Local analysis-index CI completed 43 steps with zero failures. Full logs are
retained beside this note. These runs are saved-data validation, not new native
observations, formal reruns, production adoption or deletion authority.

From repository root (replace `python3` with the selected interpreter):

```sh
sed -e "s|here=Path(__file__).resolve().parent|here=Path('$PWD/research/concurrency/singleflight_result_custody_6501_01a0ff35/repair_v2')|" -e 's|^package=.*|package=here.parent|' -e "s|here/'repair_v2/audit_v2.py'|here/'audit_v2.py'|" research/concurrency/singleflight_result_custody_6501_01a0ff35/repair_v2/source/check_repair.py.txt | python3 -
```

Repeat with `python3 -O -` for optimized mode. No formal comparison is replayed.
