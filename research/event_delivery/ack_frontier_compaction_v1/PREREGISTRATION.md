# ACK frontier after complete consumer compaction — Issue #4026

## Purpose and changed factor

Preserve #916, #926 and #3986/PR #4004. The new boundary is **all retained consumer rows being deleted by ACK**, not the count/time notification threshold or a publication repair. This is an archived SQLite model composition test relevant before future ACK/compaction adoption under #3876; it does not change the current passive reader or introduce a production queue.

## H

H1: retained-row MAX loses the accepted frontier after complete legitimate ACK; it rejects the next genuine event and can admit an old acknowledged event. H2: MAX(retained rows, persistent ACK) restores valid progress but can trust an unearned future ACK. H3: the same frontier plus an ACK-through upper bound checked in the same transaction prevents both selected failures.

## T

48 fresh cases: legacy/frontier/bounded x eight PLAN.json sequences x two repetitions. Every operation, including initialization, is a fresh CPython process opening/closing a private SQLite database. Mutations use BEGIN IMMEDIATE; a distinct parent connection reads all three tables before/after every request. Source #742 is exact Git blob 1f4f83eb51e1af3fc915ace83f0a3a4da6dbd0a6. The exact #916 contiguous reconstruction SHA256 is 7dbe43bc27ccc0d6f19b33c01e438aecd68c33753c512963d8697a426c5d35c6. Diffs expose only the frontier expression and the additional ACK upper-bound guard.

One formal invocation, exclusive directory, no case retries/replacements/tuning. Each child timeout3 seconds. Outer Python subprocess timeout30 seconds inside a45-second container call. Any unexpected nonzero child/source/timeout stops and preserves first partials. Construction is a separately retained24-case matrix with repetition99, never pooled. Current environment is the provided Linux x86_64 execution container, CPython3.13.5 / SQLite3.46.1; Docker CLI/image identity absent. No Docker/OrbStack replication, installs, GUI/input/model/provider or network experiment.

## D

All48 rows,228 operation processes, source hashes, observed table transitions, final database bytes and actual supervisor exit must reconcile. Independent audit imports none of the tested modules.

Expected directed counts: legacy has6 blocked genuine-next attempts across FULL/LATE/ACK_REPLAY,2 acknowledged-E1 readmissions,2 invalid future-ACK advances. Frontier-only has0 such liveness blocks/replays but2 future-ACK advances and2 unjustified E5 admissions. Bounded frontier has0 across all four counts. All genuine gaps stay unaccepted; late E4 then E5 works in both frontier policies; partial ACK and valid-after-bad-digest controls succeed; replayed ACK returns ACK_ALREADY_APPLIED without mutation.

PASS_ACK_FRONTIER_COMPACTION_BOUNDARY_SCOPED requires all gates. The comparator failures remain explicit. Complete contrary evidence is FAIL; source/process/evidence ambiguity is STOP/HOLD, not PASS. At least8 corruption controls must reject; the frozen auditor contains12 semantic/provenance mutations. A source-mutation negative check is also performed without rerunning the experiment.

## C

One trusted positive integer event namespace, initial accepted E1..E3, local serialized transactions. ACK represents a declared fixture acknowledgement, not model consumption, request replay authority or application success. The unbounded comparator deliberately supplies ACK-through4 while only1..3 exist. Its digest is calculated by the unchanged inherited implementation; it is not a forged runtime credential or a test against an external service.

The candidate is not a complete queue design: refused old events remain pending; automatic head disposal, general pending-position stability after interleaved arrivals, cross-session identity and real payload recoverability remain outside the tested adoption boundary. Do not infer universal queue liveness from these finite cases.

## U

No power-loss/crash durability, independent writer races, general authentication, malicious-store or distributed exactly-once claim. Software nanosecond timestamps are ordered process diagnostics, not calibrated latency data. No probability, benchmark, combined standard uncertainty or coverage factor is estimated. Separately implemented audit is by the same author, not independent human review.

## Roadmap and stop

Exact lineage -> excluded construction -> public hash freeze/readback -> one48-case allocation -> raw-only audit/negative controls -> lossless additive PR -> exact-head checks/review and main readback -> cleanup only of verified merged dependency-free owned branches through a supported operation. #3876/#57/#2789 and the global ROADMAP stay open.

## Variable/field table

| Symbol/field | Meaning | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| S | retained accepted sequence set |1| consumer.seq values |finite subset of positive integers|set of integer scalars|
| a | persistent ACK position |1|ack.last_seq|nonnegative integer, initially0|integer scalar|
| h | true historical accepted frontier |1|largest correctly accepted sequence before compaction|nonnegative integer; independently reconstructed history|integer scalar|
| f | candidate admission frontier |1|max of a and retained sequence maximum, empty maximum0|nonnegative integer|integer scalar|
| q | proposed event sequence |1|request.value for offer/retry|positive integer, frozen study1..5|integer scalar|
| b | requested ACK-through position |1|request.value for ACK|positive integer, frozen study2..4|integer scalar|
| t | diagnostic timestamp |s|monotonic_ns integer multiplied by10^-9|one same-container monotonic domain, nonnegative|integer clock sample / real seconds|
| d | content digest |not a physical quantity|SHA256 of the exact recorded bytes|64-character lowercase hexadecimal|byte/string identifier|

## Conditional argument (not a universal queue proof)

Assume initially S={1,2,3}, a=0 and h=3. Define the empty-set maximum as0. Then f=max(a,max S)=h. Suppose this invariant holds before a single serialized operation.

If a new event is admitted only at q=f+1, adding q to S and advancing h to q preserves f=h. A refusal changes neither S nor a nor h. If an ACK b is accepted only when a<b<=f and its digest matches, delete from S all entries at most b and set a=b. If b<h, the retained h is not deleted, hence f=h. If b=h, no larger accepted row exists and a becomes h, hence f=h even if S becomes empty. Exact ACK replay leaves state unchanged. Therefore these admission/ACK transitions preserve the frontier by induction, under the initial-state and single-transaction assumptions.

The retained-only comparator uses max S, so with S empty after ACK3 it obtains0 rather than h=3: q=4 is refused as a gap and q=1 can be admitted. The frontier-only comparator removes the b<=f assumption: after ACK2, a claimed ACK4 hashes the same retained E3 rows as ACK3, can set a=4 although h=3, and can admit q=5 with E4 absent. The bounded ACK check prevents that induction-breaking transition.

This argument proves only the stated sequence/ACK invariant. It does not prove producer fairness, old-head recovery, unique global event identity or physical input safety.

**Dimensional check:** a,h,f,q,b and sequence increments are dimensionless counts. The comparisons never combine them with seconds. Timestamp differences, when retained, remain integer nanoseconds converted uniformly to seconds; no timing gate decides science here.
