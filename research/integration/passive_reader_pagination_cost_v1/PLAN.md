# Issue 3985 — source-frozen pagination cost experiment

Allocation: pagination-cost-3985-20260922-01. Base main b2457b746a6df06f6536585dfe2ab937aff639f4.
Branch research/passive-reader-pagination-cost-20260922; additive namespace research/integration/passive_reader_pagination_cost_v1/.

## H/T/D/C/U
H1 (analytically determined): whole-log read plus two prefix hashes per call causes quadratic cumulative logical work at a fixed records/page setting. H2 (empirical): the median warm-local full-drain wall time of page1 divided by page32 is >=2 at 1024 records. Capacity boundary: max_bytes is the total snapshot bound, not the unread-suffix allowance.

T: exact reader and DeliveryLedger Git blobs recorded in study.py. Four sizes128/256/512/1024, page sizes1/8/32, three rotations [1,8,32], [8,32,1], [32,1,8] per size.36 separate workers. Each generates its own 256-byte-per-line stream with the actual ledger; primes the page cache with one explicit read; times one uninstrumented full drain plus an empty read; then performs the declared, untimed-for-benchmark instrumented pass. The latter delegates actual reads and hashes, never replaces their results. All complete responses retained in RAW, both passes; per-call wall/process CPU clocks and aggregate spans retained. Setup creation/priming recorded outside timing; Python import outside worker setup clock and covered only by supervisor process span, not independently decomposed.

Nine controls in final batch: page1/8/32 x exact1024 bytes,1025 bytes from start,1025 bytes with an actual reader-produced512-byte prefix cursor. One trailing space is appended past cap; original complete lines unchanged. No cursor reset, source trimming, retry or recovery implementation.

D1: PASS_PAGINATION_WORK_LAW_SCOPED only with36 exact worker cases+9 controls, every payload once/in order then empty, exact cursors and neutral flags, expected read/hash counts, instrumented/plain response equality, exact whole-cap refusals, source and actual process exits, separate raw-only audit and at least6 rejected corruption variants. D2: PASS_LOCAL_BATCHING_TIME_SCOPED only median page1/page32>=2 at1024, else HOLD; scientific mismatch FAIL, missing/infrastructure/provenance STOP/HOLD. Keep every observation, no threshold/timing-outlier edits. One immutable four-batch allocation, no replacements. Child limit10s, batch limit20s; each outer tool call encloses just one batch. Stop on failed/missing batch, retain partials. Source/gates freeze before first batch.

C: local warm-cache complete static backlog, fixed trusted producer epoch; not live producer buffering delay or concurrent writing. Larger pages batch already-available data, not collect future data. Constant line size is a controlled fixture; real variable-width streams still reread but not this exact simplified formula. Do not add a generic queue or change runtime defaults.

U: logical read bytes/hash arguments are not disk I/O, kernel reads, RSS, model calls/tokens, useful feedback, power-loss durability or security. Frequency, load and physical CPU isolation uncontrolled; guest allocation only. Three repeats give descriptive median/min/max; not a confidence bound or reliable percentile. Calibrated combined uncertainty u_c and coverage factor k unavailable. Same-clock integer ns differences, not clock-domain translation. No Docker/OrbStack identity, model/GUI/input/network experiment or production adoption.

## Exact finite work law and complete derivation

| Symbol | Meaning | Unit | Definition/domain | Type |
|---|---|---|---|---|
| N | number of complete records | 1 (count) |128/256/512/1024 |positive integer scalar|
| b | records per page |1 (count)|1/8/32; divides N |positive integer scalar|
| s | bytes in each encoded line including LF |byte (8 bits; non-SI information unit)|256 |positive integer scalar|
| L | total source length |byte|N*s |positive integer scalar|
| m | nonempty page calls |1 (count)|N/b |positive integer scalar|
| j | page index |1 (count)|1..m |positive integer scalar|
| R | logical bytes returned by read across drain+empty check |byte|sum of observed returned lengths |nonnegative integer scalar|
| Q | cumulative bytes passed to SHA256 across drain+empty check |byte|sum of observed hash input lengths |nonnegative integer scalar|

Because each invocation opens the regular source at offset zero and calls read(max_bytes+1), and L<=max_bytes, every invocation returns L bytes regardless of cursor. There are m nonempty page calls and exactly one empty check. Hence R=(m+1)L.

At page j, the consumed prefix before the call contains (j-1)b records and the returned prefix contains jb. The exact source hashes both prefixes, so this call hashes ((j-1)+j)b*s=(2j-1)b*s bytes. Summing j=1..m gives b*s*(2*m*(m+1)/2-m)=b*s*m^2=L*m. The final empty check hashes the full L-byte prefix twice, adding2L. Thus Q=(m+2)L. Substituting m=N/b and L=N*s gives R=s*N*(N/b+1) and Q=s*N*(N/b+2). At fixed b,s the leading term is s*N^2/b. No timing law follows from this operation-count law.

Dimension check: record counts and ratios are dimensionless; every term in R,Q is multiplied by s measured in bytes. Wall/CPU durations are differences of same-domain integer ns timestamps (1ns=1e-9s); they are never added to byte counts. SHA256 inputs counted here omit the once-at-import empty constant (zero bytes), fixture generation and auditor hashing.

Example (analytic, not a measured result): N=1024, s=256 gives L=262144 bytes. Page1 uses1025*L read bytes and1026*L hashed bytes; page32 uses33*L read bytes and34*L hashed bytes. This distinguishes work amplification from physical storage traffic.

## Bounded roadmap / integration handoff
1. Read current main/docs/open+closed Issues/PRs/branches; identify disjoint ownership — done before construction.
2. Reconstruct exact source and derive work law; excluded64-record/page4 construction — kept separately.
3. Freeze source, auditor, supervision, environment and this plan; post digest before measurement.
4. Four immutable one-shot batches; stop at first incomplete batch.
5. Separate raw-only auditor and corruption controls, no candidate imports; report empirical and analytic outcomes separately.
6. Publish source+lossless raw evidence through additive PR; validate actual bytes/checks/reviews/main before any promotion.
7. Delete only owned branch after verified merge and no dependent PRs; other branches untouched.

A finite source-cost result informs #3876's bounded host/session budget only. Production producer identity, host retention, ACK/presentation and same-model task benefit remain open. Closed #717 is not rewritten or re-executed. #3931/#3955 crash work and other concurrent reader studies remain separate. Full ROADMAP/#57/#3876 are not marked complete.

## Publication and source incidents
Initial GitHub create_issue lost its response; two title searches found no match, and a subsequent confirmed call created #3985. No formal invocation preceded the confirmed registration. Prior session's crash construction ZIP is only the transport for exact upstream source bytes: both Git blob IDs were recomputed and match current main. No prior experimental rows are reused. Earlier construction source study.py/batch.py remained unchanged; audit/supervisor validation edits occurred before freeze only.
