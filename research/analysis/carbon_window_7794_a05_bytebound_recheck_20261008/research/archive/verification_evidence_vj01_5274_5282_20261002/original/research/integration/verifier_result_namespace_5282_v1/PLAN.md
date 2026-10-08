# Producer-local result identity composition — #5282

## H/T/D/C/U and roadmap

H: a flat local result ID can quarantine unrelated verifier evidence. A
producer-scoped key should recover complete valid evidence without hiding
within-producer collisions or cross-producer disagreement. This tests an
explicit producer-local-ID contract, not a globally unique-ID contract.

T: 18 frozen directed cases, 75 indexed arrival permutations, every prefix,
paired BARE and PRODUCER_SCOPED adapters using identical source events and an
unchanged prepared Reducer. One provided Linux x86_64 / CPython 3.13.5
subprocess, then a separately implemented raw-only batch oracle in another
process. No model, GUI, native input, Docker/GPU or experiment network.
The original #5274 534-case/2496-schedule allocation is administratively stopped
before formal and is NOT run. Its files remain unchanged.

D: PASS_VERIFIER_LOCAL_ID_NAMESPACE_SCOPED only when all 75 raw schedules match
the independent oracle at every prefix/final, each hand-authored case disposition
agrees, sealed late results are unchanged, no authority is emitted, all source
and process evidence is complete, and all 12 effective raw-row mutations reject.
At least one complete valid case must be UNCERTAIN under BARE and PASS under
PRODUCER_SCOPED. Candidate mismatch is FAIL; incomplete/source/audit exception
is STOP/HOLD. No formal retry, exclusions, pooling or post-result changes.

C: the registry is an external trusted fixture configuration, not something
proved by a producer string. With globally unique IDs the extra namespace is
unnecessary. Duplicate-identity uncertainty is a deliberately conservative
policy. More permissive policies would be different contracts.

U: finite identity/protocol/liveness evidence only. No authentication, actual
verifier truth, ontology completeness, model quality, task effect, latency/token
saving, production runtime or global roadmap completion. Same-author independent
code is not independent human review. No statistical standard uncertainty or
coverage factor k is inferred from exhaustive synthetic cases.

Roadmap: source/corpus construction -> exact public freeze/readback -> one finite
run -> raw-only audit/mutations -> evidence PR -> applicable exact-head checks
and review -> qualified main readback. Only this successor may close; #5274,
#5273, #5267 and global ROADMAP remain separate.

## Identity and reduction contract

Registry: alpha/target, beta/effect, gamma/diagnostic, delta/target. Registry
producer names are fixed and contain no colon. A result ID is nonempty text of
at most 48 characters; baseline and candidate enforce the same restriction.
BARE passes the local ID unchanged. PRODUCER_SCOPED prepends the registered
producer and a colon. Splitting on the first colon recovers the producer and
entire local ID, even if that local ID contains colons: the encoding is injective
for this registry. This is plain namespacing, not a new inference algorithm.

The inherited reducer has two mandatory checks: target requires CURRENT and
effect requires VERIFIED_EFFECT. Optional diagnostic requires CURRENT. Message
scope is session-vj01/decision-vj01/epoch7 with subject equal to check. Evidence
roles are exact, not an implication hierarchy. Malformed/unknown producer/check
input creates uncertainty; foreign session/epoch is not current evidence.

Exact retransmission is idempotent. Conflicting payloads under one identity
quarantine that whole identity. Unopposed mandatory FAIL dominates unrelated
uncertainty. Same-check PASS/FAIL disagreement is UNCERTAIN. Otherwise all
mandatory value sets must be exactly {PASS}; optional UNKNOWN/TIMEOUT/lone FAIL
is nonblocking, optional PASS/FAIL conflict is UNCERTAIN. The full inherited
rules are in the byte-exact reducer.py and stopped preparation PLAN.md.
Sealing preserves a historical evidence cut only; it never grants live authority
or proves that every actual verifier finished. New evidence may require a new
externally versioned decision; that lifecycle is outside this fixture.

## Corpus and commands

CASES.json is the full prospective input: distinct IDs, two/three reused IDs,
retry, within-producer conflict, cross-producer disagreement, mandatory fail,
missing, wrong role, foreign epoch, unknown producer, producer/check mismatch,
optional timeout, collision plus another unopposed failure, renamed local ID,
malformed record, Boolean epoch and empty set. Permutations keep input indices
so retransmissions remain explicitly present. These are not independent samples.

```sh
python -B -m unittest test_construction -v
python -B probe.py evidence/formal01
python -B audit.py evidence/formal01 evidence/AUDIT.json
```

Outer runner: 30-second timeout and 512 MiB address-space cap for each process;
retain argv, executable/environment, source commit, stdout/stderr, exit and
monotonic start/end in FORMAL_RECEIPT.json and AUDIT_RECEIPT.json. Raw file opens
exclusively and is never overwritten. The auditor consumes raw and source only;
it imports neither candidate nor producer. Published archives must include all
input/source references, raw, receipts, construction and prior STOP records.

## Field / unit table

| Field | Meaning (Japanese) | SI unit | Definition / range | Type |
|---|---|---|---|---|
| producer | 検証器識別子 | 1 | trusted fixed registry key | string |
| rid | 検証器内の結果識別子 | 1 | nonempty, at most 48 characters | string |
| check, subject | 検証対象 | 1 | target/effect/diagnostic | enum/string |
| role | 証拠の種類 | 1 | CURRENT/VERIFIED_EFFECT/HISTORICAL/PREDICTED | enum |
| value | 観測された検証結果 | 1 | PASS/FAIL/UNKNOWN/TIMEOUT | enum |
| epoch | 対象世代 | 1 | integer7, not Boolean | scalar integer |
| session, decision | 証拠範囲 | 1 | fixed identity strings | string |
| P,F,U | 集約判定 | 1 | categorical, not numeric or confidence | enum |
| start_ns,end_ns | 実行時刻 | s, stored ns | same local monotonic clock | scalar integer |
| schedules | 到着順の件数 | 1 | exactly75 prospective rows | scalar integer |

Unit check: scope IDs/generations are never treated as time or probabilities.
Only timestamps from the same monotonic clock are compared. Wall-clock intervals
are execution receipts, not speed measurements or confidence intervals.

## Preservation / parallel work

Intake main4244aaf8b1d0ad2b26d64813842f801ce8f66612. Original construction
branch/source freeze9c2b886c5acd7069a29dad078993f3440fad5487 remains unchanged.
Comment5891230520 revealed a concurrent earlier #5274 general-reducer claimant;
comment5891528179 stops only our duplicate general allocation before formal.
No foreign branch or allocation is changed. This new question is owned by #5282
under research/integration/verifier_result_namespace_5282_v1/ on the same unique
branch. The provided container is not the shared #5085 Docker/OrbStack/GPU.

Initial direct GitHub source download failed DNS; the following source-absent
unittest failed ModuleNotFoundError. Only its unittest logs were locally saved;
the full DNS traceback is not claimed as a saved file. MCP text materialization
subsequently matched all four original Git blob hashes and passed 12 construction
tests. Namespace construction first passed6 tests. Before freeze, the key encoder
changed from JSON serialization to fixed-producer colon prefix so textual escapes
cannot exceed the inherited128-character key limit; the second construction
passed6 tests with source hashes. No full formal corpus has yet been run.
