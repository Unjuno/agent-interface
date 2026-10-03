# Versioned retained-data audit repair after independent review

The original eight-row construction and v1 source/raw/first outputs are immutable.
Nonauthor reviews 5398628964 (outside committee) and 5398632955 (assigned committee)
found five exact copied-raw witnesses accepted by v1: two delayed wrapper completions,
one premature caller delivery, one producer submitted before a request, and one
swap of the named cancelled/unaffected callers. They do not contradict the original
measured peak2 versus1 contrast. They expose missing automated causal/role joins.
V1 is historical and must not be used to claim complete causal validation.

Standalone audit_v2.py imports no v1, producer, mechanism, runner or test module.
It preserves the prior schema/count reconstruction and additionally requires:

- an attached producer's wrapper is completed before caller delivery;
- a pending, unserved request exists before producer submission, and requests
  resolve through attachment or the explicit CLOSING yield;
- each schedule's first/second/rejoin callers have their named outcomes;
- recorded platform matches original FREEZE, and UTC parses/order join the
  source-freeze and original matrix/audit command receipts.

The UTC join validates recorded metadata, not process-authenticated causality.
The new guards concern this frozen sequential event-loop registry and authored
schedules; they do not establish arbitrary trace authenticity or concurrency.

The initial explicit v1 delegate produced seven intended failures in eight raw-only
test methods; exact delegate bytes, actual UTC/exits and both private/public stream
hashes remain retained. Each causal/role fix was checked separately against the
unchanged raw. Final eight tests pass normally and with -O. Five public review
hashes reproduce exactly: v1 still accepts and v2 rejects all five. All eight prior
corruption controls still reject. Two additional UTC/platform controls reject.
No matrix, mechanism, executor, old T0 or formal allocation is executed by these
checks. audit_v2_characterize.py imports only the two auditors and raw-only tests;
that author characterization is distinct from independent nonauthor review.

FREEZE-v2.json is an ordinary post-discovery source/input freeze, written after
repair tests/characterization and before the new standalone retained audit. It
does not retrospectively preregister or replace the original experimental freeze.
RUN-v2.json contains actual command receipts. Original README/manifest bytes are
preserved under historical/; all other original package bytes remain at their
original paths. SHA256SUMS binds the final published supplement.

The v1 proposal is HOLD. New head/digest/epoch and prospective acceptance/votes by
the same fixed committee are necessary. No old vote carries forward. Current-tree
review, actual GitHub conditions and expected-old guarded history-preserving
application remain separate. No runtime, GUI/authority/effect, physical termination,
blocked-I/O deadline, cross-platform, performance or task-benefit claim is added.
