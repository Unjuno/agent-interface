# Issue #7501 A02 — source-bound provenance gate

## H / T / D / C / U

**H.** Binding typed contract clauses to exact UTF-8 byte spans, source revision, and a pinned immutable hard-background document will detect altered, ambiguous, duplicated, or stale provenance before SAT/MUS diagnosis; hard-background conflicts will block without offering a hard clause for relaxation or authorizing dispatch.

**T.** Freeze at main `18bf390d0c230b5a2ee9675cebffbc0e51bfea2d2`. Generate ten deterministic cases: valid SAT, a source-bound pair conflict, two independent MUSes in a source document, source digest mismatch, shifted span, duplicated span, stale revision, missing hard background, hard-background conflict, and one unparseable clause. Candidate and independently implemented assignment-enumerating auditor each run once. Eight isolated mutations are rejected from retained raw/result without rerunning candidate.

**D.** `PASS_PROVENANCE_BOUNDARY` only if candidate status agrees with the independent oracle on every case; valid source spans map byte-for-byte to declared clause text and revision; duplicate spans, changed digest and stale revisions fail closed; all complete conflict cores are source-linked and deletion-minimal; the pair and independent-MUS examples produce the complete expected cores; missing/contradictory hard background never becomes a relaxable choice; unknown encoding remains UNKNOWN; and dispatch/input authority are false in every row. The auditor must reject all eight mutations.

**C.** The checker receives pre-authored typed clauses and does not prove that a natural-language task was faithfully encoded. A hash proves byte identity only relative to the supplied bytes; it does not authenticate who authored them.

**U.** Deterministic finite CPU fixture only. No real contract, human explanation, natural-language parsing, GUI, model, task effect, runtime admission, or user-comprehension claim. No migration or memory/speed benefit is measured.

## Execution boundary

This is an additive successor to the merged nine-case #7501 T0 and A01 scaling test, not a replay of either. The current issue handoff explicitly names source-span/revision binding and immutable hard-background presence as the next boundary. This CPU-only method fixture needs no container semantics; it is run in Ubuntu WSL / CPython 3.12.3, not WSLc/Docker. No WSL/Docker or memory settings are changed. Exact freeze and invocation counts are in `FREEZE.md` and `RUN.md`.
