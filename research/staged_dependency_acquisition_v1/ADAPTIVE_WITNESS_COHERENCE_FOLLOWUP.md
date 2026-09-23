# Follow-up — adaptive witness reads require one coherent final-admission boundary

Status: **RETAIN coherence/atomicity requirement; FAIL sequential independent freshness.**

## Minimal fixture

Selected branch: `a == 0`.

Competitor branch: `b == 1 AND c == 1`.

Plan state: `a=0,b=0,c=0`; retained competitor witness is `b != 1`.

A writer mutation sets `b=1,c=1`, so the selected branch remains true but branch selection becomes ambiguous.

## Nontransactional schedule

For 100 repetitions:

1. checker reads selected `a=0`;
2. checker reads old witness `b=0` and treats competitor as blocked;
3. writer commits `b=c=1`;
4. checker writes effect without revalidating inside the effect boundary.

Result: **wrong effect 100/100**. Every individual read was valid at its read time, but the witness evidence no longer described the state at effect linearization.

## Transactional schedules

File-backed SQLite WAL; check and effect use one `BEGIN IMMEDIATE` transaction.

### Writer first — 50 repetitions

Writer commits `b=c=1` before checker transaction. Checker sees the competitor match and rejects: **50/50 correct rejects**.

### Checker first — 50 repetitions

Checker obtains the write transaction before the writer, validates the old state and writes the effect. The writer waits until checker commit, then applies `b=c=1`: **50/50 correct effect-first linearizations**.

Median writer wait was about 8.303 ms under the fixture's deliberate 5 ms overlap sleep. This is synchronization-fixture timing, not a product performance claim.

## Decision

Adaptive false witnesses are a semantic short-circuit only. They do not weaken the prior effect-owner atomicity requirement.

Final admission must evaluate:

`BRANCH_SELECTION / selected when + selected-action dependencies + effect authority`

against one coherent state/transaction/versioned snapshot and linearize the effect at that same boundary, or use an equivalent compare-and-swap/transaction mechanism.

Sequentially calling multiple independently fresh getters is insufficient.

## H / T / D / C / U

**H.** Witness/fallback revalidation is safe only when its component reads and the effect share one coherent final boundary.

**T.** 100 deterministic nontransactional interleavings; 50 writer-first transactions; 50 checker-first transactions using file-backed SQLite WAL.

**D.** FAIL nontransactional sequential revalidation: 100/100 wrong effects. PASS the tested atomic boundary: writer-first 50/50 rejects, checker-first 50/50 valid earlier linearizations.

**C.** A versioned snapshot plus CAS effect could provide equivalent semantics without locking; this block does not compare those implementations.

**U.** Local SQLite and deterministic scheduling only; no network transaction, GUI runtime, or latency claim.

## Next smallest experiment

The correctness chain is now complete enough for exact-runtime integration: semantic dependency membership -> unique decision validity -> proof/witness short-circuit -> coherent final admission/effect. Keep #197 as the next runtime gate rather than adding another synthetic correctness mechanism unless exact-runtime work exposes a new failure.
