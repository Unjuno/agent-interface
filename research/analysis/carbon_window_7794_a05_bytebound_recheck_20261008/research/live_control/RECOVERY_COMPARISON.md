# Recovery comparison: no observed socket reduction yet

Phase accounting of the two actual Inkscape cohorts gives a concrete negative
finding: **the helper did not reduce recovery socket exchanges**. Both used one
read. The full episode's 10-versus-8 difference is exactly the manual episode's
two-exchange malformed-save attempt. All other phase counts agree. The runtime
source manifests are byte-identical and saved task results agree, but grouping,
mistakes and decision delays differ, so these are not matched treatment arms.

| Measured quantity | Manual episode | Helper episode |
|---|---:|---:|
| Recovery reads | 1 | 1 |
| Malformed-save exchanges | 2 | 0 |
| Total socket exchanges | 10 | 8 |
| Initial capture to evaluation | 118.155 s | 75.753 s |
| Pending clock emission to recovery reply | 13.718 s | 16.371 s |

The last interval includes orchestration and decision delay; it is not pure
network latency or model inference. It supplies no evidence of faster receipt with
the helper. Do not subtract the malformed attempt's time from the old episode to
manufacture a matched comparison. Both failures and full original intervals stay
archived. `compare_recovery_accounting_v1.py` verifies counts, source equality and
result equality and writes `results/recovery-accounting-01/report.json`.

**Decision:** retain the explicit helper as checked recovery convenience; do not
promote it as a latency or round-trip optimization on this evidence. No additional
recovery mechanism is justified by these two totals alone.

## Prospective comparison v1 — registered, not executed

The machine-readable `recovery_comparison_plan_v1.json` fixes the next exploratory
eight-episode study, with four paired domain/depth cells. Every episode starts a
fresh private fixture. Domains are Inkscape legacy move-right and OpenTTD guarded
road; this tests transfer across two existing pointer fixtures, not universal
domain qualification. Inkscape starts from the same rectangle; OpenTTD uses the
same canonical guarded save. Seed labels and depth are matched within each pair.

Arms: A explicitly reads one historical clock boundary per model orchestration
call, retaining and checking the received slices; B uses the frozen pending-clock
reader to group up to four read-only exchanges in one orchestration call. Both
present the same assembled history and referenced original image when the own
clock is reached, require model review before the subsequent input, and use the
same correct task steps and caller view. No raw-versus-compact presentation change
is included as another treatment.

Depth 1 recreates the observed one-additional-read case. Depth 3 intentionally
prepares three additional historical clock boundaries to traverse before the own
clock. These are artificial recovery stress conditions, not a claim about their
real-world frequency. Verify actual records/counts; do not relabel a failed setup
to force its intended depth. All preparation happens before the measured stale
attempt, identically within a pair. Delays are not deliberately injected.

Network waits use the same 250 ms request timeout and maximum four additional
reads. The existing helper's two-second cooperative wall budget remains intrinsic
to B; A's model review between calls is not charged as socket wait. Therefore do
not compare timeout robustness under these different orchestration budgets as if
they were equivalent. Record these costs separately. A network delay/failure
remains an outcome; do not silently retry or omit it.

Primary exploratory outcome: actual recovery orchestration-call count after the
stale failure and through delivery of the own-clock history/image. Expected useful
movement is at least one fewer call in depth-3 pairs, with no increase at depth 1;
this threshold applies only to call count. Socket counts must remain visible:
grouping reads does not eliminate network exchanges. Secondary outcomes: full
capture-to-evaluation duration, stale-failure-to-reviewed-input duration where
timestamps exist, wrong/stale input, recovery errors and task correctness. Require
all paired tasks correct, no input from the recovery helper, no lost/interleaved
evidence accepted as resolved. Do not claim latency benefit without the relevant
matched endpoint evidence, or token/cost benefit without actual accounting.

Use this same model/configuration for both arms and record available identity and
output limits. Unknown settings/receipt timestamps remain missing; do not invent
them. Use the same original-image detail and full unique-record view in each pair.
If model/config changes cannot be ruled out, label the pair unqualified. Capture
source hashes before the first episode. The plan pins the currently relevant
sources; changing any treatment or gate starts v2 rather than rewriting v1.

Run all eight scheduled episodes once, retain setup failures and recoveries, then
stop for analysis. Report each paired call-count delta and elapsed-time delta,
median and range across the four pairs, with domain/depth labels. Four pairs do
not support a general performance claim; no significance or population saturation
claim follows from this sample. Any larger study needs new prospective allocation.
Actual model token/cost metrics remain unavailable until obtained from an
authoritative measurement path. This plan is not a Research Freeze declaration.
