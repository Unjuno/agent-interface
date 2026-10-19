# Cleanup identity audit and evidence custody — Issue #8681

## Initial counterexample

Synthetic A01, recorded by merged [PR #8682](https://github.com/Unjuno/agent-interface/pull/8682), is `FAIL_METHOD`. Duplicate accepted IDs masked an earlier unmatched acceptance while both `input_terminals_complete` and `input_releases_verified_empty` became true; conflicting duplicate terminal rows made empty-release evidence order-dependent. Four controls passed and three duplicate probes violated the conservative expected gate. This establishes a receipt-reconstruction defect in the synthetic component model, not that duplicate rows occur in production or that physical input was released.

## One implementation path

The broader current cleanup implementation was merged in [PR #8771](https://github.com/Unjuno/agent-interface/pull/8771). It rejects duplicate/orphan identities and malformed event records, requires unique matching accepted/terminal identity sets, and fails closed before release certification. Later synthetic regression work covered malformed accepted tokens and a valid release pair followed by malformed rows; ordinary and optimized test runs were recorded on the issue/PR history. The merged change is still component evidence only: it does not establish physical key state, live-game effect, or #59's separate live threat-control gate.

## Issue and evidence disposition (2026-10-19)

- Issue [#8681](https://github.com/Unjuno/agent-interface/issues/8681) is **closed as completed** (2026-10-18 16:14:52 UTC) for its stated synthetic cleanup-identity defect: the counterexample was retained, the broader fail-closed implementation was merged as #8771, and subsequent current-main regressions covered the malformed identity/token cases recorded in the issue. The closure comment is [#6252155468](https://github.com/Unjuno/agent-interface/issues/8681#issuecomment-6252155468). It does not close #59 or claim physical input release.
- [PR #8687](https://github.com/Unjuno/agent-interface/pull/8687) remains OPEN. Its current head `6195600931fa6de4ecf1a5012cb83b549addb5af` has 49 changed files, including 47 A02–A05 evidence files absent from #8771's merged tree; its overlapping source/test blobs differ from the merged implementation. Do not merge duplicate cleanup logic. Keep the PR/ref until the unique packages are reconciled or an explicit owner confirms another durable custody path.
- [PR #8838](https://github.com/Unjuno/agent-interface/pull/8838) remains OPEN/Draft at head `810fdcfe558ad700f779aaa66c111a4cc19eb9e4`. Its A07 focused run recorded that frozen current main failed three assertions while the candidate passed five in normal and optimized modes; the raw wrapper's failure-name classifier miscounted subtest failures. Preserve its packet and reconcile its test context before retiring the ref.
- The implementation in [PR #8771](https://github.com/Unjuno/agent-interface/pull/8771) is merged at `8af95598a2517088203be2696b043ef329ba5b5c` (merge commit `d82033921f9c2cd5a4c27f9971c46ffa0e781fb2`). It is the sole implementation path. Main's current SHA at this audit is `4e36e47a690621a658515b5107cce020dfe6df82`.

The Issue disposition and the remaining evidence-PR custody work are separate. Closing #8681 records that its defect/fix scope is complete; it does not authorize deleting branches or losing the additional A02–A07 evidence.

## Historical main-tree custody recheck (2026-10-19 03:21 UTC)

At main `3cf520498beb886750b9de8499890dfebb0ea209`, live GitHub reads still show #8681 closed, #8771 merged, and #8687 open at the head above. A direct tree comparison of `origin/main` with the exact #8687 head confirms all 47 A02–A05 packet files are absent from current main. They remain on the open PR head; no packet was copied, rerun, or altered in this recheck. Keep #8687 in `evidence-custody-hold` until the four frozen packages and their source/test provenance have a verified canonical destination. The implementation overlap must stay excluded from any evidence-only transfer.

An evidence-only preservation branch carried those four packages byte-for-byte under their original research paths plus [a separate frozen source snapshot](../../research/doom/cleanup_identity_source_snapshot_20261009/README.md). The two source/test copies are from the exact #8687 head and have SHA-256 values `5991e8761c26060ec95b835687620d86c53c2b511eaf12a723e4ab2fbc101e0c` and `03b1fee332f56a2413b6d606129a82ce09e0cd6f371d60741829f0113906b049`; all 51 manifest entries across A02–A05 matched. At this historical point the copy was still a candidate, not yet a canonical main-tree destination. No candidate or auditor was executed; focused current-main unit tests were run later for supersession review.

## Post-merge custody and supersession disposition (2026-10-19)

Evidence-only PR [#9142](https://github.com/Unjuno/agent-interface/pull/9142) merged at `9ad2614e8ad329e2aaa90487c28859718f84f647`. Main now contains the 47 A02–A05 files at their original paths and both frozen source/test blobs under the [source snapshot](../../research/doom/cleanup_identity_source_snapshot_20261009/README.md). The source/test SHA-256 values remain `5991e8761c26060ec95b835687620d86c53c2b511eaf12a723e4ab2fbc101e0c` and `03b1fee332f56a2413b6d606129a82ce09e0cd6f371d60741829f0113906b049`; all 51 original manifest entries matched before merge. No candidate, auditor, or allocation was rerun.

The only other #8687 changes were its cleanup implementation and two construction tests. Main's merged #8771 implementation rejects duplicate, invalid, and mismatched identity sets; its corresponding tests cover duplicate acceptance IDs and duplicate terminal IDs in either row order. The current-main focused module passed 27/27 in normal Python 3.11 and 27/27 under `-O`. Based on this diff and test comparison, PR [#8687](https://github.com/Unjuno/agent-interface/pull/8687) was closed as superseded at 2026-10-19 03:32:11 UTC. Its author was the authenticated repository owner; no other open PR or registered worktree used its branch. After verifying that all unique artifacts and source bytes were in main, the original remote branch was deleted. Issue #8681 remains closed for its scoped synthetic defect; #59 remains open; #8838 remains a separate open/Draft A07 custody item. None of these outcomes establishes physical release or live-game effect.

## Scope boundary

This is evidence about synthetic cleanup receipt reconstruction and test coverage. It is not physical-release evidence, proof that a live cleanup failure occurred, or permission to run a game/input experiment. Keep one implementation candidate and preserve distinct raw, audit, and source histories when retiring overlapping refs.
