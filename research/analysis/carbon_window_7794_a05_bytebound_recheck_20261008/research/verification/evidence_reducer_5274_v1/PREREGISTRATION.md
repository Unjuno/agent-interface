# Issue #5274: finite typed evidence reducer

Allocation: `evidence-reducer-5274-20260929-01`. Base main:
`4244aaf8b1d0ad2b26d64813842f801ce8f66612`.
Scope: `research/verification/evidence_reducer_5274_v1/` only.

## H / T / D / C / U

H: a union-only typed evidence frontier and an explicit immutable finalization
cut give order-independent final outcomes for the same evidence set. Optional
votes cannot overcome an unopposed mandatory failure; absent or role-ineligible
mandatory evidence cannot establish PASS. This is a deterministic contract
study, not a new algorithm or an experimental claim about verifier accuracy.

T: two mandatory checks (A: CURRENT target; B: VERIFIED_EFFECT result), one
optional CURRENT diagnostic C. The 7 states per check are missing, PASS, FAIL,
UNKNOWN, TIMEOUT, historical PASS, predicted PASS. All 343 products and all
distinct arrival permutations, plus 22 directed evidence sets, give 365 sets,
1,644 ordered cases, 4,699 prefix evaluations, and 3,288 post-seal arrivals.
Each case owns a new reducer object in one real exec'd JSONL server process.
These are finite model cases, not independent machines or real-world trials.
Exact corpus bytes are SHA-bound before the run. The fixed corpus, sources,
independent oracle and gates must be publicly frozen before one formal run.
Construction is separate; never rerun or replace the formal output directory.

D: PASS_TYPED_REDUCER_FINITE_SCOPED requires the entire frozen denominator,
zero raw-only oracle disagreements, full distinct permutation coverage,
current-role/scope checks, stable exact retransmission, conflict/unknown
preservation, no authority, immutable late/repeated seal results, normal child
exit, complete JSONL frames, exact source/wire hashes, and all twelve effective
copied-evidence controls rejected. Complete semantic disagreement is FAIL;
missing data/source/process/transport/audit is HOLD/STOP. No performance gate.

C: provisional verdicts need NOT be monotone under a total order of the labels.
For example an added current contradictory source changes provisional PASS to
UNCERTAIN. Only the evidence set grows monotonically; the final record becomes
immutable at the explicit cut. This is not proof that all outstanding real
verifiers have finished. New post-cut evidence needs a separately identified
review/decision; this prototype does not implement that scheduler.

U: fixed test schema and trusted producer mapping, one epoch/session, no live
capture age, cryptographic authentication, verifier truth, required-check
completeness, real IR integration, model, GUI, task inputs, latency/token gain,
production capability or general domain transfer. Role CURRENT is a declared
fixture field, not observed freshness. No fleet-wide environment claim.

## Exact reduction precedence

Schema: exact fields eid/check/source/session/epoch/role/status. Epoch is a
nonnegative Python int, never Boolean/float. Unknown source/check/status/role,
extra or missing fields and null evidence are malformed. Well-formed foreign
session/epoch and wrong roles are quarantined; they do not satisfy a check.
Identical canonical evidence retransmissions do not increase the frontier.
Reuse of an evidence ID with different well-formed content adds an integrity
fault, even when one version is quarantined. Raw malformed/quarantined bytes
remain in the frontier digest.

Within each check: PASS together with FAIL is CONFLICT. Otherwise any FAIL is
FAIL, even beside UNKNOWN/TIMEOUT. Exactly PASS-only support is PASS. Missing,
UNKNOWN/TIMEOUT-only, or PASS plus unresolved UNKNOWN/TIMEOUT is UNCERTAIN.
Across required A/B: an unopposed per-check FAIL determines global FAIL, even
if the other check conflicts or input is malformed. Otherwise global PASS
requires A and B PASS and zero integrity faults; all other outcomes are
UNCERTAIN. Optional C's result is retained but does not vote or veto. Thus an
optional conflict beside complete mandatory PASS does not block the required
contract. This precedence is explicit, not inferred from arrival order.

## Variables / units and proof boundary

| Field | Meaning | SI unit | Domain / definition | Type |
|---|---|---|---|---|
| A, B, C | Check identities | 1 | A/B mandatory, C optional | identifier |
| eid, source, session | Evidence/producer/session identifiers | 1 | Nonempty strings; fixed authorized mappings | string |
| epoch | Required scope generation | 1 | Nonnegative int; required value 7 in session s1 | integer scalar |
| status, role | Verifier outcome and evidence role | 1 | Enumerated exact strings above | enum |
| version | Distinct canonical messages in frontier | 1 | Nonnegative int, exact duplicates excluded | integer scalar |
| frontier_sha256 | Canonical frontier byte digest | 1 | SHA-256 of sorted canonical message strings | digest |
| start_ns, end_ns | Run chronology | second, stored as ns | Same monotonic clock, increasing integers | integer scalar |

A frontier is the set of all canonical received messages before the cut.
Set union is associative, commutative and idempotent: membership means the
message occurs at least once, independent of order and repetition. Each
classification, per-ID collision set, per-check status set, fault set and
final digest is a deterministic function of that frontier and the fixed
contract. Therefore two equal frontiers produce identical snapshots. An
unopposed required FAIL takes the first explicit global branch, so optional
PASS cannot suppress it. Missing eligible mandatory evidence cannot produce
a per-check PASS, hence cannot satisfy the global PASS branch. Seal copies a
snapshot; all subsequent add calls return before modifying the frontier, and
all returned views are copies, so later events or caller mutation cannot
rewrite that sealed snapshot. These conclusions are conditional on the
implemented operations; finite enumeration and independent oracle test their
implementation, not arbitrary external verifier truth. There is no theorem
that a provisional three-label verdict never changes.

Unit check: outcome counts/IDs/digests are dimensionless. Run-end minus
run-start has units of time. It is recorded only for process chronology, not
as a latency benefit or calibrated uncertainty. No combined u_c or coverage k
is estimated because no physical performance inference is made.

## Construction / prospective execution

Fourteen candidate unit methods passed. The first construction command omitted
--construction and stopped at the missing source-freeze prelaunch gate with
zero child calls. Its STOP and missing-execution audit are retained. Corrected
construction ran six cases (not formal). Twelve corruption designs all failed
closed; the first control harness nevertheless falsely marked the Boolean exit
mutation ineffective because dict equality equates 0 and False. That failed
control output and original controls.py are retained. Canonical typed-byte
comparison fixed only control effectiveness accounting before formal freeze;
the candidate and independent oracle were unchanged.

Run from the restored study directory: `PYTHONDONTWRITEBYTECODE=1 python run.py formal-01`.
Exactly one formal child, no retries, 20-second child timeout, outputs retained
on failure. No source change is allowed after the public freeze. Main may
advance elsewhere: the tested source is the immutable additive snapshot, not a
requirement to stall parallel work. Remote source/readback drift or an ownership
collision before launch stops this allocation.

Roadmap: source freeze -> one finite run -> raw-only audit and copied-evidence
controls -> complete evidence PR -> applicable exact-head CI and scoped review
-> main readback if qualified. #5274/#5267/global ROADMAP remain open for actual
IR/dependency/producer composition and verifier validation.
