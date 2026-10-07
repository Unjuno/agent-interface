# Compiled callback custody v4: bounded C01 CPU profile

The three callback custody changes in PR #6934 have a measurable cost on these
instrumented healthy synthetic graphs. This archive retains the complete first
measurement and separate saved-data audit. It changes no runtime or workflow.

Source comparison: named main f319439f68ff2d6451799c2ecb6b832f9b4c3a9f versus
fixed PR #6934 v4 head 5f9a3f0976e346a554ca15cf1e779bd1730e97b2. Full immutable
source images are included. Publication base is bd1697d99d5db1d1b3040de2614992776b8f81a6;
it does not change the already frozen source comparison.

The wall-time increments below are candidate minus baseline paired batch means,
in microseconds per method (eight methods per batch), median of 31 fixed signed
pairs for each graph. Ranges retain negative differences. They include Driver
construction, full trace retention and input hashing, plus counter bracketing.

| Predicates / actions | Wall median, us | Wall min..max, us | Thread-cycle counter median | Counter min..max |
|---|---:|---:|---:|---:|
| 1 / 2 | 18.7750 | -23.2875..75.9875 | 56616.25 | -63806.25..201835.25 |
| 32 / 2 | 55.6250 | -137.2875..177.7250 | 152006.75 | -371884.625..450609.5 |
| 32 / 8 | 205.7125 | -22.4125..531.6000 | 570326.375 | 10113.625..1443119.625 |

Cycle counts remain counter units. CPU_SECONDS_UNRESOLVED: they are never
converted to CPU or elapsed seconds. The official API contract is documented at
https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime .
All exact rational signed pairs are in audit-01/audit-result.json, not only medians.

## Evidence and limits

Unit compiled-custody-v4-cycles-C01-2ef3-20261003 was prospectively frozen at
08:48:08.815328 UTC and published/read back in PR #6934 comment 5967350535 before
collection. Freeze SHA256 07bb8844a8f4eee43f6d7c4437d33db31f89be40744430c3ea5881983a05812c.
The earlier preparation comment's four-input wording was corrected before the
measurement: exactly three graphs and six construction preflight methods.

Exactly one measurement invocation, 2026-10-03 08:51:14.817090 to 08:51:17.193538 UTC,
child PID 22624, exit 0. 48 warmups plus 1488 measured methods; 186 measured batches,
93 paired case rounds, 64 adjacent counter calibration pairs, 258 full raw records.
Each of all 1536 methods retains its complete input, typed receipt and callback
requests/returns. Construction preflight adds six methods outside those totals.
Separate saved-data auditor child PID 29956 exited 0 at 08:51:47.674421 UTC and
reported VALID_CHARACTERIZATION, all eight effective copied-data controls rejected,
zero zero-cycle batches. Endpoint processor IDs changed in 97/186 batches.

One Windows CPython 3.11.9 process on i7-12700H; warm correlated batches under one
unmeasured host-load/frequency/power/thermal realization. Endpoint IDs do not prove
absence of within-batch migration or preemption. Calibration is not subtracted;
the native thread cycle API measures user/kernel counter cycles. Static logical
method clock 0 is distinct from external wall timing and proves no deadline.
The 45-second timeout and 96-MiB output bound were respected; the 256-MiB working-set
target was not measured or enforced, so no peak-memory result is claimed.
Preflight native PID/start/end timestamps were not captured; later receipts do
not retroactively supply them. No original formal allocation, physical backend,
OS input, model, GPU, WSLc, shared resource, global affinity/power or main apply run.

The old v3 study by actual 32-f520 remains attributed to comments 5966915173,
5966916731 and parent #57 comment 5966993454. This study uses v4's third admission
copy, another named baseline/Python version, new batch cycle counter and complete
per-method semantic custody. It is a new bounded ordinary profile, not a rename
or replay of the old allocation. The baseline is incorrect under mutating callbacks;
its cost never justifies removing correctness checks or custody copies. Existing
0820 terminal-return diagnostic and fixed #6934 content review remain separate.
These results are no correctness, practical efficiency, adoption or application
vote. No numerical acceptance threshold or confidence interval was invented.

## Verify saved data without recollecting

All Python files have .py.txt suffixes and are inert quoted evidence. They are
not discovered as Python tests and no workflow, collector or entrypoint is added.
Read the complete auditor before deliberately invoking it. In a fresh owned copy
of this folder, verify MANIFEST.sha256, decompress measure-01/raw.jsonl.gz exclusively
to measure-01/raw.jsonl, then verify 40005771 bytes and SHA256
03d81f2f109a7445adee6f0e7675805e0e9cdfc248a9e3fea4f3094e4f310e40.
Run `python -B auditor.py.txt audit saved-audit-01` to reduce existing bytes only;
the result must equal audit-01/audit-result.json byte for byte. The auditor imports
only stdlib fractions/hashlib/json/pathlib/sys and imports no collector/runtime.
Do not invoke collector.py.txt or run_once.py.txt to repeat consumed C01 collection.

Native source/interpreter/API/input pins, first streams and receipts remain in
FREEZE.json and receipts/. PROJECTIONS.json maps every original/public byte image:
only explicit own workspace/interpreter/profile filesystem spellings are replaced with
placeholders in public receipts. Timing/semantic/PID/error bytes are unchanged;
original receipts and 40-MB raw remain preserved in the owner's private area.
The lossless gzip is exact public data, not a reconstruction from a summary.
Its 1171217 bytes have SHA256
e5fa5bd7bffc87e759d8f435554bec8804d54eb1a8654f55faa71c0eef47c640.

All 228 workflow YAML images at the named publication base were inspected for
triggers; workflow-trigger-scan.json is static inspection data, not live authority.
The global issue4242 job is restricted to a different literal head branch. The
other global map01 gate runs an unchanged deterministic two-method saved-observation
unittest, not a formal producer. No matching push trigger or workflow edits are
introduced; optional hosted CI is not claimed to have passed.

The first publication metadata pass exited 1 because its privacy guard matched
its own generic assertion literal. publication-first-error.json and the first
quoted helper preserve this definition error; the own partial archive also remains
retained privately. Only that metadata guard was repaired; no C01 collection was
repeated. Native PID/time for this publication helper were not captured.

The first staged whitespace check flagged the CR in two original Windows stdout
streams. CHECKS.json preserves that diagnostic; folder-local cr-at-eol attributes
recognize their original line endings without normalizing any evidence bytes.
