# Known terminal-accounting limitation, retained-data supplement v3

Read this note with the unchanged [first report](REPORT.md) and
[scalar correction](AUDIT_V2_NOTE.md). The author's current v2 proposal was
withdrawn before any observed eligible vote in
[HOLD5966029913](https://github.com/Unjuno/agent-interface/pull/6928#issuecomment-5966029913).
The actual frozen proposed source is old fair_v2 at
`8f5872874760b671b558a7febe4e14a23261d753`. New terminal-accounting findings in
#6896/#6924/#6907 apply to that source lineage; this package does not exercise
the subsequently revised #6913 producer or its deployed behavior.

The first report's source stats/receipt reconstruction remains reproducible,
but it is insufficient evidence of complete nominal-grid accounting or actual
observation coverage. The old source adds skipped slots when starting another
sample; it does not account for a pending interval when FINISH ends the loop.
This is a known-fault archive, with the original command/effect outcomes intact.

One exploratory ordinary reader used only retained JSON/files. It defines an
early endpoint as the recorded FINISH command, before saving the effect. At
period2ms it counts strict-interior nominal slots after the last slot already
accounted by the final source receipt. That receipt names the *oldest* due slot
and accounts its following `missed_periods_before` slots; treating its timestamp
alone as the accounted endpoint would overcount. This convention is pinned to
the retained original/proposed source, not a new definition of missed samples.

| Complete case | Source / read mode | Unaccounted strict-interior tail slots |
|---|---|---:|
| n05 | repaired polling, full read,8ms callback | 5 |
| n07 | repaired polling, one-byte read,8ms callback | 5 |
| n13 | repaired stdin, full read,8ms callback | 5 |
| n15 | repaired stdin, one-byte read,8ms callback | 6 |

All eight zero-sleep complete cases have zero such tail slots. Four original
cap64 diagnostic stops remain separate, with no substituted terminal endpoint
or coverage result. All twelve complete-case recorded miss counters still
equal their emitted-receipt sums. Recorded stats agreement therefore does not
establish complete terminal accounting. These21 descriptive slots are neither
actual missing observations nor a performance, recovery or game-effect count.
One latest-due slot may be retained rather than classed as missed by a producer
convention; this reader deliberately does not redefine that convention.

The first quick exploratory reader errored on null cutoff stats; its tool-output
transcription is explicitly marked in
[FIRST_READER_ERROR.log](supplement_v3/FIRST_READER_ERROR.log). The next first
reader and result are preserved exactly as
[terminal_reader_first.py](supplement_v3/terminal_reader_first.py) and
[RESULT_FIRST.json](supplement_v3/RESULT_FIRST.json): they overcounted fragmented
tails by ignoring the final receipt's following skip count. A source-qualified
correction, constructed after that result, yields the table above; six literal
before/exact/after-boundary checks pass. See the
[corrected reader](supplement_v3/terminal_reader.py) and
[corrected result](supplement_v3/RESULT_SOURCE_QUALIFIED.json).
Neither version is a preregistered oracle or a nonauthor review.

All125 original manifest targets, original manifest,144 v2 targets and v2
manifest bytes remain unchanged. All14 formal freeze pins, raw/first audit,
individual saved effects/scorer rows and the eight scalar-control first
acceptances remain unchanged. No old producer/native/clock/VM/game/model/formal
auditor entry point or frozen allocation was rerun. No failed case was removed,
threshold changed or source retargeted. The new manifest adds this limitation,
reader history and original v2 manifest; it does not replace either old ledger.

The four capped original / eight repaired exact FINISH outcomes and the already
qualified #6924 overlap remain descriptive evidence of the exercised service
and Linux/file-sink/fragmentation transfer. They do not justify promoting this
old scheduler as measurement-ready. New content votes must bind this known-fault
qualification and a new head/digest/epoch; old v1/v2 dispositions cannot carry.
Current tree/requirements/conditional application are separate gates. #59/R134,
useful game feedback, physical release and matched recovery remain open.

The first published v3 commit had one ignored local log missing from Git.
[PUBLICATION_FIRST_STOP.json](supplement_v3/PUBLICATION_FIRST_STOP.json) retains
that binding STOP and the first v3 manifest is preserved. The one owned log was
explicitly added before a v3 proposal; no old source/raw/manifest was changed.
