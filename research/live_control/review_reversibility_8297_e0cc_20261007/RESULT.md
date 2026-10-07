# PR 8297 retained evidence review

Root vote: **request changes**. The fixed proposal digest is
`5611b3b71618e1b9f8b6573c97ae9fa7e63851a27400c90288360b6ee655467c`.
Head `4b0d0e6f7b9553ea1a00422a777fc95e46eeab20`, review base
`9fb2dd6782d1d1477a00d14be870487fd4c54fa2`, exact composition tree
`45722f4968032b056725d32fffe9d466be490934`. Root and the existing bugbot are
genuine nonauthors of this 45-file proposal, prospectively assigned 2/2 in
PR comment 6037692071. Their worker votes are distinct; the shared GitHub
login does not represent two GitHub review identities.

## P2: Preserve and explain the A03 raw digest discrepancy

`gui_reversibility_7949_external_write_a03_20261007/STOP.md:16-17`
declares the second-call stdout as 4,311 bytes and SHA-256
`abcf391ce22ba973a0fe9abb19d15c8a03fbc606893afbf03f8a3b760d7f7e18`.
Issue 7949 comment 6037252023 repeats that digest. The exact committed
`results/candidate.raw.json` is 4,311 bytes but hashes to
`abcf391ce22ba973a0fe9abb19d15c8a03fbc606893afeb03f8a3b760d7f7e18`.
Root and bugbot independently confirmed this discrepancy. It is not resolved
by converting LF to CRLF. We have no original owner/tool evidence establishing
whether this is a copied digest error or different source bytes.

Before presenting this archive as reconciled evidence, add a correction or
custody-discrepancy record that names both digests and the committed blob,
checks original owner/tool evidence if available, and states any remaining
unknown provenance. Preserve the original STOP narrative, raw bytes, and
public record. This does not call for a candidate rerun or for promoting A03
to a scientific result. A transparent unresolved-provenance archive can be
reviewed on its explicitly narrowed claims.

## Positive saved-data result and scope

Root's separate read-only verifier recorded 91/92 checks, overall
`FAIL_READBACK` because of the A03 mismatch. The original failure remains in
`ROOT_READBACK.json`. All 45 manifest entries match the exact head blobs.
Seven A05 frozen source hashes match both the package and its public
preregistration. The A05 raw/auditor digest binding is correct.

Root's breadth-first state table and bugbot's separate reconstruction both
agree with the actual A05 rows: exactly three ordered unique cases; baseline
`restore_a` reaches `000`; the stale revision refuses recovery; refreshed
`clear_owned_a` reaches `001` and preserves external bits; the journal gap
returns UNKNOWN with null recovery and final. This establishes consistency
of these retained three-bit, horizon-one results, not general runtime behavior.

The frozen A05 `audit_core.verify` accepts duplicate case rows, a forged
emitted recovery word, and a non-null final value for an invalid-history row.
Bugbot demonstrated these with copies of saved data and the pure core; the
candidate, runner, and frozen `audit.py` entrypoint were not invoked. Actual
saved A05 output does not contain those corruptions. Disclose these limits;
do not rewrite frozen evidence or replay the consumed allocation to improve
the result. A separate successor may strengthen the auditor. Bugbot's first
broader repair request, construction error, and later calibrated addendum
are all retained.

On exact tree `45722f...`, the existing strict index checker passed for 765
retained directories, and its 22 ordinary regression tests passed. The
projection contains exact Git blobs for README, checker, unit suite and every
immediate child REPORT/FORMAL_FAILURE/STOP marker (778 files), sufficient for
the inspected checker's filesystem reads. It does not copy or run all other
scientific packages. Commands, exits, outputs, and blob hashes are retained.
Bugbot's bounded static workflow/discovery review found no existing automatic
entrypoint that executes these four packages. The detailed selection and
namespace-package limits are in `bugbot/nonexecution-review.md`; this does not
claim that a future manually targeted pytest/unittest command cannot run them.

The author reports one A05 candidate and one auditor invocation, both exit 0.
Machine-readable tool-exit/count receipts are not independently available in
this proposal. Saved mathematical consistency does not fill that gap. No GUI,
application effect, event-journal completeness, certificate authenticity,
authority, runtime admission, semantic restoration, or safety is established.

## Disposition

Both assigned reviewers request changes on the same fixed digest. There is
no approval quorum, no apply ID, and no main update. Effective platform merge
rules and a fresh integration gate are intentionally not asserted: this is a
content-review rejection, not an application attempt. Any revised proposal
requires review of its changed content; these votes do not silently transfer.
