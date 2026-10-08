# Finite command-burst / independent-scorer service — #59

The current main polling loop drains all complete lines in one read without
another scorer opportunity. The original stdin adapter samples between returned
lines, but persistent sample overruns starve input. #6896's separate repair_v2
solves that input starvation while prioritizing all already-buffered stdin lines.
This leaves a distinct observation gap under positive-cost command bursts.

The first frozen 768-row comparison uses those actual source copies, plus an
isolated one-command-per-opportunity comparator, with the same input content,
sample/callback costs and injected integer clock. A separate abstract scheduling
oracle matches every ordered event, simulated time, missed period and disposition;
all eight raw corruptions are refused. Original sources and #6896's first FAIL
are preserved unchanged. See PROTOCOL.md, SOURCE_MAP.json and FREEZE.json.

| Arm | Complete / 256 | Diagnostic stop / 256 | Largest command-start sample age |
|---|---:|---:|---:|
| original | 122 | 134 | 64.5 simulated periods |
| #6896 repair_v2 | 256 | 0 | 65.5 simulated periods |
| one_command copy | 256 | 0 | 1.5 simulated periods |

There are 90 matched conditions with lower age than repair_v2. The one_command
arm preserves all commands and owner-thread/separate-sink checks in all 256
conditions, but incurs up to 48 additional simulated periods before FINISH.
This is an observation-versus-service-cost tradeoff, not a speedup result.
It does not preempt one slow callback or recover feedback occurring inside it.

The 134 original diagnostic stops are **not all infinite starvation**. Of these,
128 have sample_cost >= period, supporting the existing sample-then-continue
starvation recurrence. Six have a half-period sample callback and a 32-command
stream; the declared 64-sample budget censors them near the end. Their first
traces remain unchanged: no extended-budget replay or favourable relabeling.

Ordinary checks after the frozen run: preserved existing scorer/adapter/clock
regressions discover 32 methods, 30 pass and two POSIX-pipe cases explicitly
skip on Windows. The first regression import preparation omitted the adjacent
progress-clock dependency; the zero-test error and minimal closure repair are
recorded separately. The original pre-freeze current-main guard also stopped
before creating raw/freeze/execution files; the subsequent inspected base update
did not consume or rerun a scientific invocation. Five literal reference checks
passed before freeze; their three literal scheduling controls are separate from
the actual source assay. The remaining checks/receipts are in execution/.

Reproduce only as new ordinary source verification with fresh output names:

```powershell
python -B assay.py new-raw.json
python -B audit.py new-raw.json new-audit.json
python -B -m unittest -v test_reference
```

These files are non-deployed research copies. Root/nested conftest files prevent
automatic pytest collection of archive/regression tests; the ordinary commands
are explicit. Do not invoke an old allocation or overwrite original raw files.

Decision: retain one_command as a minimal candidate for a real command-stream
measurement. Before deployment, establish actual burst/callback costs and test
scorer/command/finish composition with independent feedback under a separately
eligible protocol. No GUI/game/model/native input, container/WSLc, physical
release, task-effect, wall-time latency or broad runtime benefit was measured.
Windows / CPython 3.11.9 stdlib only. Main adoption and formal live gates remain
separate; this unit consumes no formal allocation and holds no shared resource.

## V2 qualification: retained policy fields do not close terminal accounting

The original README above is retained as an exact prefix and copied verbatim
to terminal_scope_v2/PRIOR_README.md. Its phrase "every ... missed period"
means agreement with **each emitted sample receipt's missed_periods_before**.
It does not mean complete nominal-deadline coverage through FINISH. The actual
assay never stored returned PollingStats or final iterator.stats. Absence of
those fields is not a captured zero, and the original policy oracle does not
independently establish terminal totals.

Later independent findings on the exact #6896 fair_v2 at 6a82a3e expose
terminal missed-period undercount: #6896 comments5965570541/5965584456 and
new known-fault descriptor5965611997. All retained source arms here, including
one_command's inherited counter, remain historical research copies; they are
not adopted as accurate final scheduler instrumentation. Runtime adoption and
accounting repair belong to #6913's actual owner and revised proposal, which
this post-hoc reader does not execute or validate.

A newly fixed raw-only reader independently enumerates nominal virtual grid
points strictly before each retained cutoff, assigning one current slot to
each emitted sample plus the preceding skips explicitly reported by its
receipt. It imports no source arm, assay or original auditor. On the unchanged
768 rows, unrepresented interior grid points occur in 19/122 original complete
rows, 130/256 repair_v2 complete rows and 72/256 one_command complete rows:
221/634 complete rows. The 134 diagnostic-budget stops are separate; 64 also
have such a point at their artificial cutoff. This is a bounded descriptive
trace/accounting diagnostic, not actual OS sampling/effect truth, a captured
final-statistic measurement, or a finding about revised #6913.

The original sample-start-to-command-start age endpoints revalidate exactly
in all768 rows. Original90 matched age contrasts, slower FINISH outcomes,
source/raw/first PASS or STOP decisions and eight controls are unchanged.
Six new literal grid expectations pass, three malformed-receipt negatives are
effective; the new retained reader runs once, exit0, with source/plan/UTC/stdout/
stderr/exit receipts. No original768-row producer, old oracle/control, ordinary
compatibility suite or formal allocation was replayed.

Preservation is the decision: retain the burst/service tradeoff with this
explicit terminal-accounting limitation. The older manifest is retained as
terminal_scope_v2/PRIOR_SHA256SUMS; the new manifest binds the complete qualified
archive. No automatic execution or deployed runtime/config changes are added.
Old v1 votes/application IDs remain historical. The material head/condition
change requires a fresh FINAL-v5 content descriptor and explicit new nonauthor
dispositions before exact-current-main combination and conditional application.
