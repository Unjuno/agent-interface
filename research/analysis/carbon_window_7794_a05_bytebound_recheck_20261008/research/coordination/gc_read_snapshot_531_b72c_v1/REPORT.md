# Atomic retirement does not make split recovery reads one snapshot

## Decision and delivery status

**PASS_GC_READ_SNAPSHOT_BOUNDARY_SCOPED** for allocation
`gc-read-snapshot-531-b72c-20260922-01`:40 fresh cases,120 read-only
classifications,80 actual reader/writer child processes, four immutable
10-case batches. All actors and batch children exited0. No timeout, formal
rerun, replacement, exclusion or post-result source change occurred.

**Publication remains HOLD_GITHUB_WRITE_TOOLS_UNAVAILABLE.** GitHub MCP was
used to read current main, README, CURRENT_GOAL, ROADMAP, open/closed issue
lineage, recent PRs and125 returned branch names. The full exposed48-action
schema contains no write operation. Plugin discovery returned the installed
GitHub; the supplied container has no gh/docker or configured GH_TOKEN /
GITHUB_TOKEN. No remote Issue, branch, PR, merge, CI launch or branch deletion
was performed. This is a local publication constraint, not a fleet-wide
failure or a separate research objective. Sources and gates were frozen and
announced before formal collection locally, not publicly registered on GitHub.

Initial and final checked main:
`e4c2e58122aa138e421048d8e86ec18259143b9e`. Proposed unique publication path
`research/coordination/gc_read_snapshot_531_b72c_v1/` returned404 at that exact
main; proposed remote branch search returned no match. The local patch still
requires actual repository review and integration checks. No full main
checkout, repository-wide test, remote CI result or completed merge is claimed.

## H / T / D / C / U

**H.** The previous a61e study varied process-crash write ordering. This study
holds retirement to one atomic transaction and varies the READER transaction
extent. Two separately completed SELECTs can combine old metadata with new
history, or vice versa, even though the writer only commits complete states.
One read transaction should retain a single committed snapshot.

**T.** The unchanged #531 WatermarkLedger source is copied exactly (3639bytes,
Git blob24329aaedf166b98a5babf5cfb9c61af7c6f40f0). Each private SQLite WAL
store begins after A/1,B/2,C/3 with capacity2: generation4, retirement watermark1,
history B/2+C/3. A separate writer atomically deletes both history rows and
advances watermark to3. It admits no new operation. A separate read-only
process retrieves meta/history with AUTOCOMMIT or SNAPSHOT, in both component
orders and five barrier-directed schedules, two repetitions each. Before-open,
after-BEGIN-before-first-SELECT, between-SELECTs and after-SELECTs placements
are distinguished; STABLE is the no-write control. The snapshot policy uses
BEGIN DEFERRED and closes the transaction after both SELECTs/classification.

**D.** All40/120 source, state, SQL, wire, process and batch gates pass. Independent
raw audit exits0, errors=[],12/12 evidence-corruption controls reject. Baseline
mixed-view count4, rebound-old proposals2, genuine-next refusals2. Candidate
all three counts0 across20 cases. No actual action/effect is dispatched based
on any classifier result. The unsafe comparator remains unsuitable for this
coherent-recovery contract despite the hypothesis PASS.

**C.** WAL permits the writer to commit while the read snapshot remains open.
That mode differs from a61e's DELETE-journal crash experiment, so no pooled
cross-run comparison is made. Complete atomic writes alone are not a promise
that independently completed reads occur at the same logical instant. This
new persistence/reading adapter is NOT asserted to be present in production;
it is not a SQLite defect. The #531 pure model never claimed database recovery
or concurrent reads. A strong downstream current-state admission check could
still refuse a proposal; none is bypassed or evaluated here.

**U.** No crash/power-loss, simultaneous admissions, multiple compactors, issuer
restart/rollback, malicious storage, input safety, real GUI effects, model
choice, token savings, latency benefit, production promotion or arbitrary
backend behavior is established. Two repetitions are directed finite coverage,
not a natural race rate. Separate audit means independent implementation and
process by the same author, not independent human review. Calibrated combined
timing uncertainty and a coverage factor are unavailable; timestamps are only
same-container order/operational diagnostics.

## Formal results

| Reader policy | Cases | Mixed committed-state views | REBOUND_OLD classified NEW_INTENT_ALLOWED | Genuine FRESH incorrectly refused | Old coherent view despite newer final DB |
|---|---:|---:|---:|---:|---:|
| AUTOCOMMIT |20|4|2|2|4|
| SNAPSHOT |20|0|0|0|8|

The four baseline mixtures are BETWEEN_READS in both orders, twice. Only the
two META_FIRST mixtures change the tested rebound/fresh classification. The
HISTORY_FIRST mixtures are still not a single writer-committed state, even
though these two classifications happen not to be wrong. Do not equate
inconsistency count4 with harmful-classification count2.

The exact original B/2 request never becomes NEW_INTENT_ALLOWED in any case.
Its original generation2-to3 protects it in the harmful mixed state. The
REBOUND_OLD control deliberately keeps B/2 identity but changes generation to
4-to5; report it as identity rebinding, not unchanged-wire replay. All120
outcomes are classifications only. This experiment measured zero replayed GUI
operations and does NOT observe duplicate business effects.

AFTER_BEGIN gives the new state in all eight policy/order/repetition cases,
including all four SNAPSHOT cases. BEGIN DEFERRED alone has not yet selected a
data snapshot. BETWEEN_READS and AFTER_READS SNAPSHOT cases return the old
coherent state in all eight cases even though compaction has committed before
return. These are honestly historical reads, not falsely current authority.

## Complete conditional explanation

Field definitions, domains, types and units are tabulated in PREREG.md. The
code's next-sequence value is the last retained sequence plus one, or the
retirement watermark plus one when history is empty. Every quantity is a
dimensionless ordinal; no elapsed time is used as a retirement sequence.

1. Before compaction the last retained sequence is3, so next is4.
2. After compaction history is empty but the watermark is3, so next is also4.
3. META_FIRST with the writer between SELECTs sees old watermark1 and new empty
   history. Next therefore becomes2. B/2 rebound to current generation4-to5
   passes the unchanged model's sequence/generation checks. Genuine D/4
   exceeds next2 and is SEQUENCE_GAP. Exact old B/2 fails generation validation.
4. HISTORY_FIRST sees old B,C history and new watermark3. This is another mixed
   pair, but the retained tail still makes next4. Retained B-content checks
   refuse rebinding, and genuine D remains eligible. Hence merely counting
   classifier errors misses some inconsistent snapshots.
5. Under one read transaction, SQLite WAL snapshot isolation preserves the
   committed state selected by the first SELECT through the second. Both
   complete writer states yield next4 and no rebound acceptance. The first
   SELECT, not the BEGIN acknowledgement, chooses that state; the AFTER_BEGIN
   control tests this exact distinction.
6. That argument is conditional on the stated database isolation and connection
   configuration. It proves no latest-at-return or read-to-action atomicity.
   The observed historical returns explicitly delimit the result.

This is a known transactional composition principle, not a novel SQLite
mechanism. Primary documentation: SQLite Isolation
https://www.sqlite.org/isolation.html and Transaction (DEFERRED and implicit
transaction completion) https://www.sqlite.org/lang_transaction.html.
The experiment tests the concrete process/SQL/rehydration behavior and exact
archived model at that boundary rather than inferring it from a state table.

## Evidence and audit

Every case retains exact per-actor input/output/error bytes, process arguments,
PIDs and true wait statuses, per-command monotonic brackets, actual SQL trace,
query-only reader total_changes0, returned components, classifier requests and
results, and independent before/after-write/final database observations. SQLite
backup files are explicitly labelled DERIVED coherent snapshots; the final
original store and surviving sidecars are retained separately. No backup is
misrepresented as a byte-for-byte original WAL file.

The separately structured auditor imports no actor, runner or vendor. It
reconstructs four possible read states, expected operations/order and outcomes,
opens all retained databases read-only, joins actual wire bytes to retained
records, checks strict Boolean/integer distinctions and source freeze, and
checks externally observed batch exits. Original formal evidence764 files is
byte-identical before/after audit. All11 frozen file digests remain exact.
Ten offline unit methods pass. All80 actor and four batch-child PIDs were absent
on a later /proc check; the actual wait receipts, not absence alone, establish
exit completion. No unrelated process was signalled.

Twelve corruptions reject: missing/duplicate case; Boolean repetition;
watermark alteration; dropped history; false fresh refusal; authority mutation;
Boolean exit; missing process; missing SQL evidence; request sequence mutation;
changed final state. These finite controls are not a proof of arbitrary auditor
soundness or adversarial authenticity.

## Preserved construction incident and predecessor

construction-01 ran once: six sessions/18 classifications, exit0. Its first
auditor's drop_history mutation selected an already-empty history, so it was a
no-op and was correctly not rejected. The original auditor and failed output
are preserved in construction-auditor-v1/. Before formal freeze only the control
selection was repaired to target a nonempty history. Read-only construction
reaudit passed all12 mutations; the construction experiment was not rerun.

The inherited a61e archive is included unchanged as PREDECESSOR_A61E.tar.xz:
104924bytes, SHA256
fc406d0cbdf58fc46dc6fd0f7620bb3315c9d29ac0ec3fba0313745e4a7b6a65.
Its fresh read-only reaudit reproduces the original AUDIT bytes. Old formal
reexecutions0; none of its30/90 rows is pooled into this40/120 allocation.
Previous publication-unavailable statements remain historically preserved.

## Integrity

| Artifact | SHA256 |
|---|---|
| FREEZE.json |0d60d890406085fabc47830a08aec0020dddb2a6e1d97e9e416f329cc6eddf1c|
| FORMAL_ALL.jsonl |94aa25ad4565dd63810d5749dd2285d0f5506b425ca95412f0840861183867b2|
| AUDIT.json |48930301b596129cb76c842c48f824509974ffe4aa3618c9d3ca9c3db7eaf2b9|

FORMAL_ALL is a labelled ordered concatenation of four original RAW.jsonl
files, not another execution or replacement of originals. Hashes bind bytes,
not source authenticity or formal public registration.

## Non-overlap and integration handoff

#4037 changes the prefix deleted while a NEW intent is concurrently admitted.
This allocation admits no new intent and retires a fixed complete history.
#3929 changes writer version/membership publication and already snapshots its
reader inside one transaction. #4027 changes missing-outcome interpretation
after completed retirement. #4026 changes event ACK-frontier validation.
Their sources, branches, gates and results are untouched. No whole-repository
absence of unpushed work is claimed from bounded searches.

The decision relevant to #24/#2084/#2789 is: restoring an intent ledger requires
both coherent writer publication and coherent reader acquisition of history,
retirement information and generation. Preserve the restored snapshot's role
as historical evidence. Any actual later input admission still requires its
own current-state/fresh-authority check. Do not integrate the AUTOCOMMIT adapter
as if atomic writer publication automatically supplied that guarantee.

Bounded research roadmap: intake, predecessor byte verification, excluded
construction, local prospective source freeze,40-case execution, raw-only
audit/corruptions and byte recheck COMPLETE. Remote successor/PR/CI/main and
remote branch cleanup NOT PERFORMED. A local additive patch and complete
archive are handoff artifacts, not a claimed merge. Full global roadmap,
production recovery and model/task acceptance are not completed here.

## Read-only revalidation

After extracting this complete study into a new directory:

```sh
python -B audit.py --controls
python -B test_contract.py
```

Audit the saved result only. Do not rerun execute.py/run.py with the consumed
allocation. No experiment is executed by the separate publication unpacker.
